# test_notion.py
import unittest
from unittest.mock import MagicMock, patch
from notion_lib import NotionManager

class TestNotionManager(unittest.TestCase):
    
    def setUp(self):
        self.bot = NotionManager("fake_token")

    @patch('notion_lib.requests.post')
    def test_create_project_success(self, mock_post):
        # Simuliamo una risposta 200 OK da Notion
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "new_project_id"}
        mock_post.return_value = mock_response

        # Eseguiamo
        proj_id = self.bot.create_project("Test Project", area_name=None)
        
        # Verifichiamo
        self.assertEqual(proj_id, "new_project_id")
        self.assertTrue(mock_post.called)

    @patch('notion_lib.requests.post')
    def test_create_task_fail(self, mock_post):
        # Simuliamo errore 400
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        # Verifichiamo che lanci l'eccezione
        with self.assertRaises(Exception):
            self.bot.create_task("Test Task", "Backend", "proj_id")

if __name__ == '__main__':
    unittest.main()
