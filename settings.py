"""Settings Class"""
import logging
import functions as fn


class Settings:
    """Setting class contains information for GUI of Finance Manager v3.0"""

    def __init__(self, file):
        """Create Settings class using file (db, sqlite) given in file variable"""
        self.file = file
        logging.debug(f"Creating Settings class using {self.file}")

        all_settings = fn.get_data_from_database(self.file, "SELECT * FROM settings")
        for setting in all_settings:
            self.__setattr__(setting[0], setting[1])
            logging.debug(f"Setting {setting[0]} to {setting[1]}")

        self.codes = self.get_codes()
        logging.debug("Code loaded from settings file")

    def get_setting(self, setting):
        """Get setting value"""
        return self.__dict__[setting]

    def set_setting(self, setting, value):
        """Change setting value in class"""
        self.__dict__[setting] = value

    def save_settings(self):
        """Save settings to database"""

        for setting in self.__dict__:
            query = f"UPDATE settings SET value='{self.get_setting(setting)}' WHERE setting='{setting}'"
            fn.update_database(self.file, query)

    def get_codes(self):
        """Load income and outcome codes from settings file; returns dict"""

        return {
            "income": fn.get_data_from_database(self.file, "SELECT * FROM income"),
            "outcome": fn.get_data_from_database(self.file, "SELECT * FROM outcome")
        }

    def get_income_codes(self):
        """Returns income codes only (no description)"""
        return [str(i[0]) for i in self.codes["income"]]

    def get_outcome_codes(self):
        """Returns outcome codes only (no description)"""
        return [str(i[0]) for i in self.codes["outcome"]]

    def get_code_desc(self, table, code):
        """Return description of code for given code and table"""
        return fn.get_data_from_database(self.file, f"SELECT * FROM {table} WHERE code = {code}")[0][1]

    def __str__(self):
        string = ""
        for i in self.__dict__:
            string += f"{i} = {self.__dict__[i]}\n"
        return string


if __name__ == '__main__':
    settings = Settings(file='bin/settings.db')
