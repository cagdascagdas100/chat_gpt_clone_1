# TerraYield / AAYS — Python Maliyet Motoru Demo

Bu klasör, kullanıcı seçimlerine göre İngiltere/Londra odaklı yapı maliyeti satırları üretir.

## Desteklenen yapı türleri

- Müstakil Ev
- Apartman
- Perakende
- Karma
- Sanayi

Sanayi için 10 alt tür `terrayield_cost_engine_demo.py` içindeki `INDUSTRIAL_SUBTYPES` listesinde tanımlıdır.

## Manuel çalıştırma

```powershell
python .\terrayield_cost_engine_demo.py --input-json .\sample_inputs\detached_london_250m2.json --output-json .\output_detached.json
```

Interactive mod:

```powershell
python .\terrayield_cost_engine_demo.py --interactive --output-json .\output_interactive.json
```

## Runner ile çalışma

Mevcut PowerShell runner şu task dosyasını okur:

```text
ai-tasks/current-task.json
```

Bu demo için runner script’i:

```text
ai-task-scripts/terrayield_cost_engine_051_smoke_test_20260520.ps1
```

Runner sonuçları otomatik olarak `ai-results/terrayield_cost_engine/` altına yazar ve GitHub’a push eder.

## Doğruluk skalası

- 4/4: resmi kaynak, BCIS export veya proje özel quote.
- 3/4: profesyonel benchmark.
- 2/4: model allocation.
- 1/4: quote gerektiren provisional satır.

## Güvenlik

Bu demo production DB’ye yazmaz, SQL/migration çalıştırmaz, secret basmaz.
