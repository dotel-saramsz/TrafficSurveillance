# TrafficSurveillance
Minor Project on Vehicle Detection and Congestion Mapping
Follow the project structure

---- Note, for the web sockets to function,additional dependencies are required ----
1. Django Channels v1.0.2
2. asgi_redis v1.0.0
3. daphne v1.0.0
4. asgiref v0.13
5. redis v2.1
6. autobahn v0.18
7. twisted v16.2

---- Please note the latest version of Django Channels v2.x has significant code and architecture update and hence the code is incompatible with v2.x. Similarly, the other libraries are also compatible only with channels v1.x.

---- Install in the following order (because automatic dependency fetch from package installers like pip will download the incompatible latest versions:
pip install twisted==16.2

pip install autobahn==0.18

pip install redis==2.1

pip install asgiref==0.13

pip install daphne==1.0.0

pip asgi_redis==1.0.0

pip install channels==1.0.2
