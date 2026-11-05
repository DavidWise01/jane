import importlib.util, json, pathlib, tempfile, unittest
p=pathlib.Path(__file__).with_name("jane-b160-ecosystem-observer.py")
spec=importlib.util.spec_from_file_location("b160_observer",p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Observer(unittest.TestCase):
 def repo(self,name,**kw):
  return {"name":name,"full_name":"DavidWise01/"+name,"owner":{"login":"DavidWise01"},"private":False,"archived":False,"disabled":False,"description":None,"fork":False,"has_pages":False,"default_branch":"main","pushed_at":"2026-11-01T00:00:00Z",**kw}
 def test_public_scope(self):
  data=m.build([self.repo("a"),{**self.repo("b"),"private":True},{**self.repo("c"),"owner":{"login":"SomeoneElse"}}],True)
  self.assertEqual(data["counts"]["observed"],1)
  self.assertEqual(data["repositories"][0]["name"],"a")
  self.assertEqual(data["governance"]["automatedCrossRepoWrites"],False)
 def test_proposals_not_mutations(self):
  r=self.repo("new")
  data=m.build([r],True)
  self.assertIn("SUGGEST_DESCRIPTION",data["repositories"][0]["proposals"])
  self.assertIn("CONSIDER_PAGES_WHEN_APPLICABLE",data["repositories"][0]["proposals"])
  self.assertEqual(r["description"],None)
 def test_archive(self):
  r=self.repo("archive");r["archived"]=True
  self.assertEqual(m.proposals(r),["ARCHIVED_OBSERVE_ONLY"])
 def test_stable_sort(self):
  data=m.build([self.repo("z"),self.repo("a")],False)
  self.assertEqual([r["name"] for r in data["repositories"]],["a","z"])
  self.assertFalse(data["complete"])
if __name__=="__main__":unittest.main()
