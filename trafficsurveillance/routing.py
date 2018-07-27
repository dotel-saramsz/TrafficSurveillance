from channels import route
from surveillanceapp import consumers

channel_routing = [
    route('websocket.connect', consumers.ws_connect, path=r'^/video/(?P<videoid>.*)$'),
    route('websocket.disconnect', consumers.ws_disconnect, path=r'^/video/(?P<videoid>.*)$'),
    route('websocket.receive', consumers.ws_receive, path=r'^/video/(?P<videoid>.*)$')
]