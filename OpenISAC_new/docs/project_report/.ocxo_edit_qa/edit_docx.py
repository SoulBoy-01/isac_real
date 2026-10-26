from pathlib import Path
from zipfile import ZipFile
from lxml import etree
import re,shutil,json,sys,tempfile
sys.path.insert(0,str(Path(tempfile.gettempdir())/'openisac-docx-edit-deps'))
base=Path(r'D:\isac\OpenISAC_new\docs\project_report')
qa=base/'.ocxo_edit_qa'
src=base/'OpenISAC_项目验收报告.docx';backup=qa/'original.docx'
figsrc=(base/'gen_figs.py').read_text('utf8').replace('OCXO','外部时钟').replace('(USB DAC → 外部时钟 VADJ)','(USB DAC → 外部时钟\\nVADJ)')
namespace={'__name__':'diagram_rebuild','__file__':str(base/'gen_figs.py')}
exec(compile(figsrc,'gen_figs.py','exec'),namespace)
namespace['OUT']=str(qa)
for fn in ['fig_sys_arch','fig_soft_ue','fig_flow_ue']:namespace[fn]()
figmap={}
with ZipFile(backup) as z:
 for name in ['fig_sys_arch.png','fig_soft_ue.png','fig_flow_ue.png']:
  old=(base/'figs'/name).read_bytes()
  matches=[n for n in z.namelist() if n.startswith('word/media/') and z.read(n)==old]
  assert len(matches)==1,(name,matches)
  figmap[matches[0]]=(qa/name).read_bytes()
 replacements=[('外部恒温晶振（OCXO）','外部时钟'),('恒温晶振（OCXO，10 MHz）','外部时钟（10 MHz）'),('本地 OCXO ','外部时钟'),('本地 OCXO','外部时钟'),('OCXO 调整','外部时钟调整'),('OCXO 控制电压','外部时钟控制电压'),('驯服 OCXO','驯服外部时钟'),('本地晶振','外部时钟'),('收发双端独立晶振','收发双端独立外部时钟')]
 pattern=re.compile('|'.join(re.escape(a) for a,b in replacements)+r'|OCXO',re.I)
 nsxml={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
 changes=[];out=qa/'modified.docx'
 with ZipFile(out,'w') as target:
  for info in z.infolist():
   data=z.read(info.filename)
   if info.filename in figmap:data=figmap[info.filename]
   elif info.filename.endswith('.xml'):
    root=etree.fromstring(data);modified=False
    for para in root.findall('.//w:p',nsxml):
     nodes=para.findall('.//w:t',nsxml)+para.findall('.//w:delText',nsxml)
     text=''.join(n.text or '' for n in nodes);found=list(pattern.finditer(text))
     for m in reversed(found):
      value=next((b for a,b in replacements if a.lower()==m.group().lower()),'外部时钟')
      starts=[];offset=0
      for n in nodes:starts.append(offset);offset+=len(n.text or '')
      i=next(i for i,n in enumerate(nodes) if starts[i]<=m.start()<starts[i]+len(n.text or ''))
      j=next(i for i,n in enumerate(nodes) if starts[i]<m.end()<=starts[i]+len(n.text or ''))
      first=nodes[i].text or '';last=nodes[j].text or ''
      if i==j:nodes[i].text=first[:m.start()-starts[i]]+value+first[m.end()-starts[i]:]
      else:
       nodes[i].text=first[:m.start()-starts[i]]+value
       for k in range(i+1,j):nodes[k].text=''
       nodes[j].text=last[m.end()-starts[j]:]
      modified=True
     if found:changes.append({'before':text,'after':''.join(n.text or '' for n in nodes)})
    if modified:data=etree.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
   target.writestr(info,data)
 with ZipFile(out) as check:
  assert check.testzip() is None
  for n in check.namelist():
   if n.endswith('.xml'):assert not re.search('ocxo|恒温晶振|本地晶振',check.read(n).decode('utf8'),re.I),n
 try:shutil.copyfile(out,src);final=src
 except PermissionError:
  final=base/'OpenISAC_项目验收报告_外部时钟版.docx';shutil.copyfile(out,final)
 print(json.dumps({'output':str(final),'text_paragraphs_updated':len(changes),'diagrams_updated':len(figmap),'changes':changes},ensure_ascii=False,indent=2))
 (qa/'changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),'utf8')
 (qa/'output_path.txt').write_text(str(final),'utf8')
