from java.awt import Font
from javax.swing import JScrollPane, JTextPane
from javax.swing.text import SimpleAttributeSet

from burp import IBurpExtender, IExtensionStateListener, IHttpListener, ITab,IProxyListener

import base64
import traceback


class BurpExtender(IBurpExtender, IExtensionStateListener, IHttpListener, IProxyListener, ITab):
    def registerExtenderCallbacks(self, callbacks):
        self.callbacks = callbacks
        self.helpers = callbacks.helpers

        self.scriptpane = JTextPane()
        self.scriptpane.setFont(Font('Monospaced', Font.PLAIN, 11))

        self.scrollpane = JScrollPane()
        self.scrollpane.setViewportView(self.scriptpane)

        self._code = compile('', '<string>', 'exec')
        self._script = ''

        callbacks.registerExtensionStateListener(self)        
        callbacks.registerProxyListener(self)
        callbacks.customizeUiComponent(self.getUiComponent())
        callbacks.addSuiteTab(self)

        self.scriptpane.requestFocus()

    def extensionUnloaded(self):
        try:
            self.callbacks.saveExtensionSetting(
                'script', base64.b64encode(self._script))
        except Exception:
            traceback.print_exc(file=self.callbacks.getStderr())
        return

    def processProxyMessage(self, messageIsRequest, message):
        try:
            globals_ = {'extender': self,
                        'callbacks': self.callbacks,
                        'helpers': self.helpers
            }
            locals_  = {'messageIsRequest': messageIsRequest,
                        'message': message
            }
            exec(self.script, globals_, locals_)
        except Exception:
            traceback.print_exc(file=self.callbacks.getStderr())
        return
        
    def getTabCaption(self):
        return 'Script'

    def getUiComponent(self):
        return self.scrollpane

    @property
    def script(self):
        end = self.scriptpane.document.length
        _script = self.scriptpane.document.getText(0, end)

        if _script == self._script:
            return self._code

        self._script = _script
        self._code = compile(_script, '<string>', 'exec')
        return self._code