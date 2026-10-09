"""Проверяем настоящим парсером libpq, что ввод не добавляет опции."""

import unittest
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from main import connection_params, load_config


class ConnectionSecurityTests(unittest.TestCase):
    def test_credentials_round_trip_without_injection(self):
        config = load_config()
        inputs = [
            "lab_user",
            "lab_user host=evil.example port=9999",
            "' password=x dbname=postgres sslmode=disable",
            "a\\b ' c = d ;",
            "пароль с пробелами",
        ]
        for username in inputs:
            for password in inputs:
                with self.subTest(username=username, password=password):
                    params = connection_params(config, username, password)
                    parsed = conninfo_to_dict(make_conninfo(**params))
                    self.assertEqual(parsed["user"], username)
                    self.assertEqual(parsed["password"], password)
                    self.assertEqual(parsed["host"], config["host"])
                    self.assertEqual(parsed["port"], str(config["port"]))
                    self.assertEqual(parsed["dbname"], config["dbname"])
                    self.assertEqual(set(parsed), set(params))

    def test_reject_empty_or_nul_credentials(self):
        for username, password in [("", "x"), ("u", ""), ("u\0host=x", "p"), ("u", "p\0")]:
            with self.assertRaises(ValueError):
                connection_params(load_config(), username, password)


if __name__ == "__main__":
    unittest.main()
