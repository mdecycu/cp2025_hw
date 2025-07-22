# Run static server
import static
from gevent.pywsgi import WSGIServer

http_server = WSGIServer(('0.0.0.0', 8081), static.app)
http_server.serve_forever()