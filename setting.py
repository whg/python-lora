from inflection import underscore

class BadSettingError(Exception):
    def __init__(self, s, cls):
        super().__init__(f'Bad setting {s} for {cls.__name__}')

class SettingNotFoundError(Exception):
    def __init__(self, s, cls):
        options = ', '.join([o for o in cls.options if o])
        super().__init__(f"Can't find {s} for {cls.__name__}, valid options are: {options}")

class Setting:
    shift = 0
    mask = 0xff
    num_bytes = 1
    
    @classmethod
    def encode(cls, s):
        if hasattr(cls, 'forward_transform'):
            return cls.forward_transform(s)

        if hasattr(cls, 'options'):
            options = cls.options
            numeric = all([o.isnumeric() for o in options if o is not None])

            if type(s) is int:
                if numeric:
                    s = str(s)
                else:
                    return s

            try:
                return cls.options.index(s)
            except ValueError:
                pass
            raise SettingNotFoundError(s, cls)            
            
        if type(s) is int or type(s) is bool:
            return s

        raise BadSettingError(s, cls)            

    @classmethod
    def decode(cls, value):
        if hasattr(cls, 'options'):
            # IndexError won't happen
            return cls.options[value]
        elif hasattr(cls, 'reverse_transform'):
            return cls.reverse_transform(value)
        
        return value
    
    @classmethod
    def id(cls):
        return underscore(cls.__name__)
