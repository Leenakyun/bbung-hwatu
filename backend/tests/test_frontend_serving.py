import unittest

import app as app_module


class FrontendServingTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config.update(
            TESTING=True
        )

        self.client = (
            app_module.app.test_client()
        )

    def test_root_serves_frontend_index(self):
        response = self.client.get(
            "/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        body = response.get_data(
            as_text=True
        )

        self.assertIn(
            "우리 집 룰 그대로",
            body,
        )
        self.assertIn(
            "/css/style.css",
            body,
        )
        self.assertIn(
            "/js/app.js",
            body,
        )

    def test_css_is_served_from_frontend_folder(self):
        response = self.client.get(
            "/css/style.css"
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertIn(
            "font-family",
            response.get_data(
                as_text=True
            ),
        )


    def test_hwatu_card_asset_is_served(self):
        response = self.client.get(
            "/assets/cards/1_1.png"
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.mimetype,
            "image/png",
        )

    def test_javascript_is_served_from_frontend_folder(self):
        response = self.client.get(
            "/js/app.js"
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertIn(
            "connectRealtime",
            response.get_data(
                as_text=True
            ),
        )


if __name__ == "__main__":
    unittest.main()
