#!/usr/bin/python

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *
from PyQt4.QtNetwork import QNetworkCookieJar
from PyQt4.QtNetwork import QNetworkCookie
from argparse import ArgumentParser
import os
import sys
import time

debugMode = False

class TimerThread(QThread):
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.exiting = False
        self.timeout = 0
        
    def __del__(self):
        self.exiting = True
        self.wait()
        
    def run(self):
        print "waiting " + str(self.timeout) + " sec"
        self.sleep(self.timeout)
        
    def runtimer(self, time):
        self.timeout = time
        self.start()
        
class TimeoutThread(QThread):
    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.exiting = False
        self.timeout = 0
        
    def __del__(self):
        self.exiting = True
        self.wait()
        
    def run(self):
        self.sleep(self.timeout)
        
        print "timeout reached.. exiting"
        self.quit()
        
    def start_timeout_thread(self, timeout):
        self.timeout = timeout
        self.start()

class WebKitRenderer(QObject):
    def __init__(self, filename, wait, url, type, username, password, height, width):
        
        QWebPage.javaScriptAlert = self.alert_handler
        QWebPage.javaScriptConfirm = self.confirm_handler
        
        self.filename = filename
        self.wait = wait
        self.type = type
        self.username = username
        self.password = password
        self.authenticationTried = False
        self.height = height
        self.width = width
        
        self.app = QApplication(sys.argv)
        self.view = QWebView()
        self.page = QWebPage()
        self.view.setPage(self.page)
        self.timer = TimerThread()
        
        #self.view.resize(QSize(1024,768))
        
        self.page.settings().setAttribute(QWebSettings.JavascriptEnabled, True)
        self.page.settings().setAttribute(QWebSettings.PluginsEnabled, False)
        self.page.settings().setAttribute(QWebSettings.PrivateBrowsingEnabled, True)
        self.page.settings().setAttribute(QWebSettings.JavascriptCanOpenWindows, False)
        self.page.settings().setAttribute(QWebSettings.DnsPrefetchEnabled, True)
        
        self.page.mainFrame().setScrollBarPolicy(Qt.Horizontal, Qt.ScrollBarAlwaysOff)
        self.page.mainFrame().setScrollBarPolicy(Qt.Vertical, Qt.ScrollBarAlwaysOff)
        
        self.connect(self.page, SIGNAL("loadFinished(bool)"), self.on_load_finished)
        self.connect(self.page, SIGNAL("loadStarted()"), self.on_load_started)
        self.connect(self.page, SIGNAL("loadProgress(int)"), self.on_progress_changed)
        self.connect(self.page.networkAccessManager(), SIGNAL("authenticationRequired(QNetworkReply*, QAuthenticator*)"), self.on_auth_required)
        # self.connect(self.page.networkAccessManager(), SIGNAL("sslErrors(QNetworkReply *,const QList&)"), self.on_ssl_errors)
        self.connect(self.timer, SIGNAL("finished()"), self.saveImage)
        
        self.view.load(QUrl(url))
        self.view.show()
        
        
    def saveImage(self):
        size = self.page.mainFrame().contentsSize()
        self.view.resize(size)
        
        print "saving image..."
        try:
            image = QImage(self.page.viewportSize(), QImage.Format_ARGB32)
            painter = QPainter()
            painter.begin(image)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.TextAntialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
            self.page.mainFrame().render(painter)
            painter.end()
            
            
            self.scale_image(image).save('.'.join([self.filename, self.type]), self.type)
        except StandardError, e:
            print e
        self.app.exit()
        
    def scale_image(self, image):
        if self.width > 0 or self.height > 0:
            image = image.scaled(self.width,self.height,Qt.KeepAspectRatio)
        return image
        
    def on_auth_required(self, networkReply, authenticator):
        if self.authenticationTried:
            self.app.exit()
        print "authentication required..."
        self.authenticationTried = True
        authenticator.setUser(self.username)
        authenticator.setPassword(self.password)
    
    def on_progress_changed(self, progress):
        if debugMode:
            print str(progress) + "% loaded"

    def on_load_started(self):
        print "starting page load..."
        self.statusCheckerThread = TimeoutThread()
        self.statusCheckerThread.start_timeout_thread(30)
    
    def on_load_finished(self, result):
        print "load finished with result: " + str(result)
        print "bytes received: " + str(self.page.bytesReceived())

        if not result:
            sys.exit()

#        uncomment this code if you would like to see the html being retrieved from the given URL. This can be very large
        if debugMode:
            print str(self.page.mainFrame().toHtml().toAscii())
        
        self.timer.runtimer(self.wait)
        
    def alert_handler(self, frame, msg):
        print "a javascript alert dialog was fired with msg: " + msg
        
    def confirm_handler(self, frame, msg):
        print "a javascript confirm dialog was fired with msg: " + msg
        return True
        
    def on_ssl_errors(self, reply, errors):
        """Slot that writes SSL warnings into the log but ignores them."""
        for e in errors:
            print "SSL: " + e.errorString()
        reply.ignoreSslErrors()
        

if __name__ == '__main__':
    usage = """%prog [options] """
    
    parser = ArgumentParser(usage, version="%prog 0.1")
    parser.add_argument('url', help="The url to generate a screenshot from")
    parser.add_argument("-x", "--xvfb", action="store_true", dest="xvfb",
                         help="Start an 'xvfb' instance. Use this options for 'headless' mode")
    parser.add_argument("-d", "--display", dest="display",
                         help="Connect to the specified x-server to render", metavar="DISPLAY")
    parser.add_argument("-o", "--filename", dest="filename",
                         help="The filename of the resulting image file",
                         default="webkitimg", metavar="FILE")
    parser.add_argument("-t", "--type", dest="type",
                         help="The image type of the output file",
                         default="jpg", choices=['bmp', 'gif', 'jpg', 'jpeg', 'png', 'tiff'])
    parser.add_argument("-w", "--wait", dest="wait", type=int,
                         help="Time in seconds before rendering the target URL as an image.",
                         metavar="SECONDS", default=0)
    parser.add_argument("-u", "--user", dest="user", nargs=2,
                      help="Username and password", metavar="USERNAME PASSWORD", default=["user","pass"])
    parser.add_argument("-r", "--ratio", dest="ratio", nargs=2, type=int,
                      help="Scale the resulting image to the dimension provided. \
                      The aspect ratio is always kept. 0 forces auto-scaling (this is the default behavior) \
                      Example: -r HEIGHT WIDTH",
                      metavar="HEIGHT WIDTH", default=[0,0])
    parser.add_argument("--debug", action="store_true", dest="debug",
                         help="output to console with extra content")
    
    #parse command line args
    options = parser.parse_args()
    # if len(args) != 1:
        # parser.error("incorrect number of args")
    if options.xvfb and options.display:
        parser.error("-x and -d are mutually exclusive")
    # options.url = args[0]

    if options.xvfb:
        # Start 'xvfb' instance by replacing the current process
        newArgs = ["xvfb-run", "-a", "--server-args=-screen 0 1600x1800x24", "python"]
        for i in range(0, len(sys.argv)):
            if sys.argv[i] not in ["-x", "--xvfb"]:
                newArgs.append(sys.argv[i])
        os.execvp(newArgs[0], newArgs)
        raise RuntimeError("Failed to execute '%s'" % newArgs[0])

    if options.display:
        os.environ["DISPLAY"] = options.display
        
    debugMode = options.debug
        
    if not debugMode:
        saveout = sys.stdout
        fsock = open('logs/Qt.log', 'w')
        sys.stdout = fsock
        
    renderer = WebKitRenderer(options.filename, 
                              options.wait, 
                              options.url,
                              options.type,
                              options.user[0],
                              options.user[1],
                              options.ratio[0],
                              options.ratio[1])
    sys.exit(renderer.app.exec_())
