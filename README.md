# Flask项目中集成Celery

[Celery](https://docs.celeryproject.org/en/latest/index.html)是一个简单高效的实时分布式任务队列系统，我们可以将一些耗时比较长或者计算密集的任务交给celery处理，它也支持定时任务类似于crontab。而web应用中可以将一些任务丢给celery异步处理，比如发邮件消息推送、模型推理等。简单的Flask应用集成Celery比简单，有[官方文档](https://flask.palletsprojects.com/en/1.1.x/patterns/celery/)可做参考，可较复杂的flask应用如使用了蓝图(blueprint)分了很多模块的怎么组织celery和各种任务就比较复杂官方也没有说明文档，一不小心就会陷入循环导入。下面就介绍一种celery集成方法。

官方文档[demo](https://flask.palletsprojects.com/en/1.1.x/patterns/celery/#configure)中有一个`make_celery`的函数

```python
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
```

这个函数主要用来创建Celery对象，并从flask上更新一些配置加入上下文环境，像文档上单文件是不会出问题的返回的celery对象直接在下面定义任务，然后集成到路由中。如果你flask app是使用[app factories](https://flask.palletsprojects.com/en/1.1.x/patterns/appfactories/)和蓝图(blueprint)，那在这里定义的task又怎么在路由中引用呢，这就会导致循环引用问题。

我们可以把`make_celery`拆开来，首先创建celery对象然后等flask app初始化完成后在更新配置，这就解决问题了，任务单独放在`tasks.py`文件中也便于管理和查看

先来看最终项目结构图，就是flask web项目加入了celery

```shell
flask-celery-demo
├── app
│   ├── api
│   │   ├── __init__.py
│   │   └── views.py                # 视图
│   ├── __init__.py
│   └── tasks.py                    # celery任务
├── config.py
├── requirements.txt
├── run.sh
└── service.py                       # 应用入口
```
先解释下主要`service.py`创建celery对象，然后把对象传入`app/__init__.py`文件中的`create_app`函数在里面更新celery配置。`app/tasks.py`单独存放给celery的任务，视图函数也可以方便导入。下面一个个文件说明

先来看`service.py`文件也是整个应用的主入口

```python
from app import create_app

def make_celery(app_name):
    broker = getattr(config[os.getenv('FLASK_ENV') or 'default'], "CELERY_BROKER_URL")
    backend = getattr(config[os.getenv('FLASK_ENV') or 'default'], "CELERY_BACKEND_URL")

    celery = Celery(
        app_name,
        broker=broker,
        backend=backend
    )

    return celery


# share celery object
my_celery = make_celery(__name__)

flask_app = create_app(os.getenv('FLASK_ENV') or 'default', celery=my_celery)
```

这里的`make_celery`函数只返回celery对象未更新配置，供`tasks.py`导入，并传给`create_app`，接下来看`app/__init__.py`文件

```python
def create_app(config_name, **kwargs):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # initial celery
    if kwargs.get('celery'):
        init_celery(kwargs['celery'], app)

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')

    return app


def init_celery(celery: Celery, app: Flask) -> None:
    """
    initial celery object wraps the task execution in an application context
    """
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
```

`init_celery`函数就是最上面官方文档中`make_celery`中剩下的部分，用于更新配置加入上下文， `create_app`函数已经很熟悉了不多做介绍，只增加了一个celery参数在里面调用`init_celery`初始化celery对象

然后看`tasks.py`

```python
from service import my_celery as celery

@celery.task()
def log(message: Any) -> Any:
    return message
```

这个文件单独定义各celery任务，最后看视图函数怎么调用`app/api/views.py`文件

```python
from app.tasks import log

@api.route("/hello-world")
def hello_world():
    result = log.delay('hello world')
    try:
        r = result.get(timeout=3)
    except TimeoutError:
        r = 'celery run failed'
    return jsonify({"info": r})
```

以上就是所有需要注意的地方了，整套代码托管在[github](https://github.com/fangjh13/flask-celery-demo)可查阅

## 运行demo

本示例中包含了docker文件，可以在docker环境方便的启动

首先clone项目，docker-compose启动就可以

```shell
git clone https://github.com/fangjh13/flask-celery-demo.git
docker-compose build
docker-compose up
```

这里消息代理使用的是redis在`config.py`中配置，还写了个定时任务也在`config.py`中启动后每隔1分钟有输出信息，docker-compose会启动四个容器分别是flask服务、celery worker、celery beat和redis服务。当然也可以启动多个celery worker如

```shell
docker-compose up --scale worker=2
```

## Reference

1. [flask.palletsprojects.com](https://flask.palletsprojects.com/en/1.1.x/patterns/celery/)
2. [medium.com](https://medium.com/@frassetto.stefano/flask-celery-howto-d106958a15fe)

