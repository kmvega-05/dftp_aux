from app.processing.handlers._noop import handle_noop
from app.processing.handlers._pass import handle_pass
from app.processing.handlers._quit import handle_quit
from app.processing.handlers._rein import handle_rein
from app.processing.handlers._syst import handle_syst
from app.processing.handlers._user import handle_user


HANDLERS_FTP_COMMANDS = {
    "NOOP" : handle_noop,
    "SYST" : handle_syst,
    "USER" : handle_user,
    "PASS" : handle_pass,
    "QUIT" : handle_quit,
    "REIN" : handle_rein
} 