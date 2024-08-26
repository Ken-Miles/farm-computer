import logging

logger = logging.getLogger('computer')
handler = logging.FileHandler(filename='computer.log', encoding='utf-8', mode='a')
dt_fmt='%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

# class Logger:
#     time_color = colorama.Fore.LIGHTBLACK_EX
#     time_format = '%Y-%m-%d %H:%M:%S'

#     info_color = colorama.Fore.LIGHTBLUE_EX
#     warn_color = colorama.Fore.LIGHTYELLOW_EX
#     error_color = colorama.Fore.LIGHTRED_EX

    
#     type_col_dict = {
#         'info': info_color,
#         'warn': warn_color,
#         'error': error_color
#     }
    
#     name_color = colorama.Fore.LIGHTMAGENTA_EX


#     def __init__(self, name: str):
#         self.name = name

#     def __Log(
#         self,
#         message: str,
#         type: str
#     ):
#         if type in self.type_col_dict:
#             type_color = self.type_col_dict[type]
#         else:
#             type_color = self.info_color

#         print(
#             f'{self.time_color}{time.strftime(self.time_format)}{colorama.Fore.RESET} '
#             f'{type_color}{type.upper()}{colorama.Fore.RESET}{" " * ((5 - len(type)) + 4)}'
#             f'{self.name_color}{self.name}{colorama.Fore.RESET} '
#             f'{message}'
#         )

#     def info(self, message: str):
#         self.__Log(message, 'info')

#     def warn(self, message: str):
#         self.__Log(message, 'warn')

#     def error(self, message: str):
#         self.__Log(message, 'error')

class Logger:
    _logger: logging.Logger = logger

    def __init__(self, logger: logging.Logger=None, name: str=None, ):
        if name: 
            self.name = name
        if logger: 
            self._logger = logger
    
    def info(self, message: str):
        self._logger.info(f'{message}')
    
    def warn(self, message: str):
        self._logger.warning(f'{message}')
    
    def error(self, message: str):
        self._logger.error(f'{message}')

    def debug(self, message: str):
        self._logger.debug(f'{message}')
    
    