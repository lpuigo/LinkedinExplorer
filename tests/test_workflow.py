import unittest
from collections import deque
from app.core.models import Personne, PersonStatus
from app.core.services import WorkflowManager
from app.core.repository import PersonRepository

class MockRepository(PersonRepository):
    def __init__(self):
        self.saved_persons = {}
    
    def load_existing_persons(self):
        return list(self.saved_persons.values())
    
    def save_person(self, person: Personne):
        self.saved_persons[person.url] = person

class TestWorkflow(unittest.TestCase):
    def setUp(self):
        self.repo = MockRepository()
        self.workflow = WorkflowManager(self.repo)

    def test_add_person_deduplication(self):
        p1 = self.workflow.add_person("https://www.linkedin.com/in/user1")
        self.assertIsNotNone(p1)
        self.assertEqual(len(self.workflow.queue), 1)
        
        # Test doublon
        p2 = self.workflow.add_person("https://www.linkedin.com/in/user1")
        self.assertIsNone(p2)
        self.assertEqual(len(self.workflow.queue), 1)

    def test_workflow_steps(self):
        p = self.workflow.add_person("https://www.linkedin.com/in/user2", "ref_url")
        self.assertEqual(p.statut, PersonStatus.A_TRAITER)
        
        # Next
        next_p = self.workflow.get_next_person()
        self.assertEqual(next_p, p)
        self.assertEqual(next_p.statut, PersonStatus.EN_COURS)
        self.assertEqual(self.workflow.current_person, p)
        
        # Decision: Interest
        self.workflow.set_current_person_decision(True)
        self.assertEqual(p.statut, PersonStatus.ANALYSE_INTERRESSANT)
        self.assertIn(p.url, self.repo.saved_persons)
        
    def test_decision_ignorer(self):
        p = self.workflow.add_person("https://www.linkedin.com/in/user3")
        self.workflow.get_next_person()
        
        # Decision: Pas intéressé
        self.workflow.set_current_person_decision(False)
        self.assertEqual(p.statut, PersonStatus.ANALYSE_NON_INTERRESSANT)
        # Ne doit pas être sauvegardé dans le repo (selon la logique implémentée)
        self.assertNotIn(p.url, self.repo.saved_persons)

    def test_update_info(self):
        p = self.workflow.add_person("https://www.linkedin.com/in/user4")
        self.workflow.get_next_person()
        
        info = {
            "nom": "Jean",
            "titre": "Dev",
            "societe": "Corp",
            "lieu": "Paris"
        }
        self.workflow.update_current_person_info(info)
        self.assertEqual(p.nom, "Jean")
        self.assertEqual(p.titre, "Dev")

if __name__ == '__main__':
    unittest.main()
