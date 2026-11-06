"""실제 앱 연결로 다른 종류의 사진을 검색하고 원시 점수를 기록한다."""
from pathlib import Path
import gc
import json
import os
import shutil
import sys
import tempfile

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
sys.dont_write_bytecode = True

project = Path(__file__).resolve().parents[2]
output = Path(__file__).resolve().parent
images = output/'images'
images.mkdir(exist_ok=True)
scratch = output/'temp'
scratch.mkdir(exist_ok=True)
tempfile.tempdir = str(scratch)
sys.path.insert(0,str(project))

# 기존 에셋은 그대로 두고, 공부용 테스트 폴더에 복사한다.
sources = {name:project/'assets/images'/name for name in ('Test1.jpg','Test2.jpg','Test3.jpg')}
sources.update({name:Path(r'C:\computerVision\images')/name
                for name in ('beach.jpg','road.png','seal.jpg','zebra.png')})
for name,source in sources.items():
    shutil.copyfile(source,images/name)

from app import build_service

print('LOADING_REAL_APP_MODELS',flush=True)
service = build_service()
try:
    documents,failures = service.analyze(images)
    assert len(documents)==7 and not failures,(len(documents),failures)
    print('ANALYZED_7_IMAGES',flush=True)
    queries = ['고양이','누워있는 고양이','하품하는 고양이','해변','도로','물개','얼룩말','자동차']
    results = {}
    for query in queries:
        # 기본 5개 제한을 늘려, 관련 없는 이미지까지 전체 순위를 확인한다.
        hits = service.search(query,top_k=len(documents),mode='images')
        results[query] = [{'file':info.file_name,'score':float(score)} for info,score in hits]
        print(json.dumps({'query':query,'ranking':results[query]},ensure_ascii=True),flush=True)

    data = {'date':'2026-11-03','model':'xlm-roberta-base-ViT-B-32',
            'pretrained':'laion5b_s13b_b90k','score':'raw cosine similarity',
            'image_sources':{name:str(path) for name,path in sources.items()},'results':results}
    (output/'results.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    cats = {'Test1.jpg','Test2.jpg','Test3.jpg'}
    labels = {'Test1.jpg':'고양이','Test2.jpg':'누워 하품하는 고양이','Test3.jpg':'고양이 얼굴',
              'beach.jpg':'해변','road.png':'도로','seal.jpg':'물개','zebra.png':'얼룩말'}
    report = ['# 이미지 검색 비교 결과\n\n',
              '기준: 2026-11-03. 실제 앱의 로더·인코더·임시 유사도 비교·DB 연결을 그대로 사용했다.\n',
              '고양이 3장과 실습용 해변·도로·물개·얼룩말 4장, 총 7장을 비교했다. 점수 변환이나 제외 기준은 적용하지 않았다.\n',
              '원본 에셋은 바꾸지 않았다. 이 폴더와 이미지는 study 안에 보관하며 GitHub 업로드에서 제외한다.\n\n']
    for query in queries[:2]:
        report.extend([f'## 검색어: {query}\n\n','| 순위 | 사진 | 내용 | 원시 코사인 점수 |\n','|---|---|---|---:|\n'])
        for rank,hit in enumerate(results[query],1):
            name=hit['file']
            report.append(f"| {rank} | [{name}](images/{name}) | {labels[name]} | {hit['score']:.4f} |\n")
        cat_min = min(hit['score'] for hit in results[query] if hit['file'] in cats)
        other_max = max(hit['score'] for hit in results[query] if hit['file'] not in cats)
        report.append(f'\n고양이 최저 점수: {cat_min:.4f}, 비고양이 최고 점수: {other_max:.4f}, 차이: {cat_min-other_max:.4f}.\n\n')
    report.extend(['## 다른 검색어의 1위\n\n','| 검색어 | 1위 파일 | 점수 |\n','|---|---|---:|\n'])
    for query in queries[2:]:
        first=results[query][0]
        report.append(f"| {query} | {first['file']} | {first['score']:.4f} |\n")
    report.extend(['\n## 해석할 때 주의할 점\n\n',
                   '- 고양이와 비고양이가 점수로 구분되는지 확인하는 소규모 점검이다. 전체 검색 품질을 보장하지 않는다.\n',
                   '- 고양이 3장은 같은 개체이고 비고양이 표본도 적다. 이 결과로 보편적인 제외 점수를 정할 수 없다.\n',
                   '- 누워 있는 자세가 뚜렷한 Test2가 누워있는 고양이 검색에서 몇 위인지 확인한다. 얼굴만 나온 사진의 자세를 단정하지 않는다.\n',
                   '- 자동차는 이 7장에 없다. 그래도 결과가 나오는 것은 현재 코드가 점수순으로 정렬만 하고 관련 없는 결과를 제외하지 않기 때문이다.\n',
                   '- 코사인 점수는 확률이 아니다. 점수에 배수를 곱하거나 softmax로 바꿔도 모델의 구분 성능 자체가 좋아지지는 않는다.\n\n',
                   '[전체 원시 결과](results.json) · [재실행 코드](check_search.py)\n'])
    (output/'결과.md').write_text(''.join(report),encoding='utf-8')
finally:
    gc.collect()
    service.session_directory.cleanup()
print('RESULT_FILES_WRITTEN',flush=True)
