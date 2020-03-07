Kanban
=======

Kanban - fork from Chimera - a  Kanban application.
- 客户端是用JavaScript和Angular框架编写的；
- 服务器是用Python和Tornado框架编写的；
- MongoDB用于数据存储；

项目结构
-----------------

该项目在结构上由两部分组成-客户端和服务器。
客户端脚本，模板和样式放置在系统的公共部分，必须由Web服务器（nginx）提供对其的访问。
服务器部分作为一个整体应用程序封装在python中，可通过REST API对其进行访问。

```
app - 服务端脚本 python/tornado (backend)
│
├─ documents - MongoDB document-model
├─ handlers - Tornado handlers
└─ system - Chimera system files
    └─ utils - System modules


www -网页端脚本 chimera
│
├─ resources - jquery/bootstrap/underscore/...
└─ system - Client-side

```

tornado提供了获取有关http请求方法的信息的能力，例如：get，post，put，delete，head，options，patch。应用程序的结果将是JSON格式的响应。

REST Endpoint
----------------------

路由位于服务器应用程序配置文件中
```app/system/configuration.py```

JSON响应结构
---------------------

在处理每个请求的过程中，服务器应用程序迟早会引发异常以宣布工作已完成。异常可能是计划中的错误处理，并且在正常操作中未提供致命错误的情况下，应用程序将基于有关已发生事故的可用数据生成异常。无论如何，所有异常都是 __ResultMessage__ 类的包装器，该类为每个请求返回相同的数据结构。


```app/system/utils/result.py```

```json
{
    "error": {
        "message": "error_message",
        "code": "error_code"
    },
    "content": {},
}
```

* error - 有关错误的信息块;
* error.message - 文本错误信息（默认为“”）;
* error.code - 条件错误代码（默认为0）;
* content - 对任意结构的请求的正确响应块（默认为{}）;

安装方式
---------

#### Requirements

Python 3.5 参见 requirements.txt

#### Web server

为了使该应用程序正常运行，您必须按域提供访问权限 (例如 www.kanban.local).

##### hosts

    # 访问客户端程序，服务器应用程序 по REST API
    127.0.0.1 www.kanban.local

##### nginx

为了使域正常工作，您需要配置Web服务器（例如，nginx）。nginx的配置示例

```
# public
server {
    listen 80;
    charset utf-8;
    root /path/to/kanban/www;
    server_name www.kanban.local;
    index index.html;
    client_max_body_size 5M;

    location / {
        try_files $uri /index.html;
    }

    location ~ \.(js|css|ico|htm|html|json)$ {
        try_files $uri =404;
    }

    location /_/ {
        proxy_pass_header Server;
        proxy_set_header Host $http_host;
        proxy_redirect off;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Scheme $scheme;
        proxy_pass http://backend_kanban;
    }
}

# api
upstream backend_kanban {
    server 127.0.0.1:8888;
}
```


#### Backend

MongoDB用作DBMS（测试在3.0.7版上进行）。可以在以下位置配置对MongoDB数据库的访问权限以及龙卷风应用程序路由
 ```app/system/configuration.py```

对于MongoDB，您需要定义一个数据库-默认情况下，连接将进入看板数据库中的localhost：27017


#### Frontend

对客户端库的访问在主索引文件中配置， ```www/public/index.html```
在大多数外部库中都是通过第三方CDN连接的，并且系统的内部库具有相对路径。

您可以在角度客户端应用程序的主模块中配置对服务器的客户端访问， ```www/public/system/app.js```
在其中需要确保参数

        baseUrl: "http://www.kanban.local/_",
        baseWWWUrl: "http://www.kanban.local"

根据Web服务器的设置进行配置。
- baseUrl - 应用程序API的基本URL
- baseWWWUrl - 应用程序客户端资源的基本URL

特点
-----------

系统实现了用于创建board，card列表，任务的基本功能。可以使用可排序的jQuery UI插件拖放任务，以及添加用户来控制开发板。安全问题不在此实现范围之内。

安装系统后，启动应用程序python app/main.py并转到地址（默认为www.kanban.local）并进行注册。如果未使用用户名，则将使用指定的密码创建用户。
