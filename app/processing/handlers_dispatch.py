from app.processing.handlers._cdup import handle_cdup
from app.processing.handlers._cwd import handle_cwd
from app.processing.handlers._dele import handle_dele
from app.processing.handlers._mkd import handle_mkd
from app.processing.handlers._noop import handle_noop
from app.processing.handlers._pass import handle_pass
from app.processing.handlers._pwd import handle_pwd
from app.processing.handlers._quit import handle_quit
from app.processing.handlers._rein import handle_rein
from app.processing.handlers._rmd import handle_rmd
from app.processing.handlers._rnfr import handle_rnfr
from app.processing.handlers._rnto import handle_rnto
from app.processing.handlers._syst import handle_syst
from app.processing.handlers._user import handle_user


HANDLERS_FTP_COMMANDS = {
    "CDUP" : handle_cdup,
    "CWD"  : handle_cwd,
    "DELE" : handle_dele,
    "MKD"  : handle_mkd,
    "NOOP" : handle_noop,
    "PASS" : handle_pass,
    "PWD"  : handle_pwd,
    "QUIT" : handle_quit,
    "REIN" : handle_rein,
    "RMD"  : handle_rmd,
    "RNFR" : handle_rnfr,
    "RNTO" : handle_rnto,
    "SYST" : handle_syst,
    "USER" : handle_user,
} 