# DNA17 V0.1.3 — Чекор по чекор: GitHub → верификација → Zenodo

Редоследот е фиксен: **GitHub pre-release → независна верификација → финален release → Zenodo DOI.**
Zenodo доаѓа последен, бидејќи записот таму е трајен и не може да се менува.

---

## Чекор 0 — Твоја ратификација (пред качување)
1. Прочитај го `DECISIONS.md`. Таму се седумте одлуки D1–D7.
2. Кажи му на Claude кои ги прифаќаш, кои ги менуваш и кој е датумот.
3. Claude го пополнува блокот за потпис и го пресметува `MANIFEST.sha256` повторно со скрипта. Хешовите никогаш не се пишуваат рачно.

> Зошто ова е пред качувањето: ако `DECISIONS.md` го смениш директно на GitHub, неговиот хеш се менува и CI ќе падне на проверката на манифестот. Тоа е намерно, бидејќи ништо не смее да се смени без нов хеш.

## Чекор 1 — Создај репозиториум (подобро на компјутер)
1. Отвори github.com, најавен како **eit-orbitos**.
2. Горе десно кликни **+** → **New repository**.
3. За **Repository name** внеси `nova-q-eit-dna17-voxel`.
4. Избери **Public**. Кај јавните репозиториуми GitHub Actions е бесплатен. Кај приватните се трошат минути, а macOS тестовите трошат повеќе. Лиценцата PolyForm Noncommercial ја штити комерцијалната употреба и кога кодот е јавен.
5. **НЕ** штиклирај README, .gitignore ни License, бидејќи пакетот веќе ги има.
6. Кликни **Create repository**.

## Чекор 2 — Качи ги фајловите
1. Распакувај го ZIP-от на компјутер. Ќе добиеш папка `nova-q-eit-dna17-voxel`.
2. Вклучи прикажување скриени фајлови, за да се видат `.github` и `.gitattributes`.
   - **Windows:** File Explorer → View → Show → Hidden items.
   - **Mac:** во Finder притисни Cmd + Shift + .
3. На GitHub кликни **uploading an existing file**.
4. Повлечи ја **содржината** на папката, не самата папка. Тоа се сите фајлови и потпапки, вклучувајќи ги `.github` и `.gitattributes`.
5. Во **Commit changes** напиши: `DNA17 V0.1.3 release candidate`. Потоа кликни **Commit changes**.

На телефон не може да се качуваат папки. Ако си само на телефон, кажи ми и ќе ти ги дадам фајловите еден по еден, со точната патека за **Add file → Create new file**.

## Чекор 3 — Провери дека CI е зелен
1. Отвори го табот **Actions** → **CI**.
2. Почекај 2–5 минути. Треба да има **9 зелени** работи: 3 оперативни системи × 3 Python верзии.
3. Секоја работа проверува три нешта:
   - SHA-256 манифестот: сите фајлови совпаѓаат, 0 unlisted;
   - 71 тест, вклучувајќи го fuzz-тестот со 4.070 мутанти;
   - 24 проби.
4. Ако нешто е црвено, отвори ја работата, копирај го логот и прати ми го.

## Чекор 4 — Pre-release (кандидат)
1. Од десната страна на репозиториумот кликни **Releases** → **Draft a new release**.
2. Кај **Choose a tag** внеси `v0.1.3-rc1` и кликни **Create new tag**.
3. За **Title** внеси `DNA17 V0.1.3 — release candidate 1`.
4. Штиклирај **Set as a pre-release**.
5. Кликни **Publish release**. GitHub сам прикачува **Source code (zip)**.

## Чекор 5 — Независна верификација
1. Преземи го **Source code (zip)** од release-от.
2. Испрати го на независен проверувач (Kimi или ревизорот) со следнава задача:

```
Распакувај, па изврши од главната папка:
  python scripts/manifest.py verify
  PYTHONPATH=src python -m unittest discover -s tests -v
  python -I -B probes/probes_equivalent.py
Пријави: манифест N/N, тестови 71/71, проби 24/24, исклучоци 0.
Не менувај ништо. Секој наод → нова верзија.
```

Ако проверувачот најде дефект, правиме V0.1.4 и се враќаме на чекор 3.

## Чекор 6 — Финален release
1. Кога верификацијата е PASS, направи нов release со tag `v0.1.3`.
2. Овој пат **не** го штиклирај pre-release.
3. Во описот запиши го резултатот од верификацијата и SHA-256 на ZIP-от.

## Чекор 7 — Zenodo (рачно, за лиценцата да биде точна)
Препорачувам рачно качување наместо автоматска GitHub–Zenodo интеграција. Така ти лично ги потврдуваш лиценцата и метаподатоците пред DOI.

1. Отвори zenodo.org, најавен како **Stobensium**, и кликни **New upload**.
2. Качи го **Source code (zip)** од финалниот release `v0.1.3`.
3. Пополни ги полињата:

| Поле | Вредност |
|---|---|
| Resource type | Software |
| Title | NOVA Q / EIT — DNA17 Voxel Validator |
| Creators | Mladenovski, Toni · ORCID 0009-0009-8343-662X · EITNetworks LLC (Independent Researcher) |
| Version | 0.1.3 |
| Description | текстот од `abstract` во `CITATION.cff` + „Software claim only; no physical claim.“ |
| License | PolyForm Noncommercial 1.0.0. Ако ја нема во листата, избери опција за друга или сопствена лиценца, а во описот наведи: „Software: PolyForm Noncommercial 1.0.0; documentation: CC BY-NC-SA 4.0; commercial use by written agreement: info@eitnetworks.org“. |
| Related works | https://github.com/eit-orbitos/nova-q-eit-dna17-voxel · *is supplemented by* |
| Keywords | NOVA Q, EIT, DNA17, voxel, dynamic topology, AI memory architecture |

4. Провери ја секоја вредност, па кликни **Publish**. Ќе добиеш DOI.

## Чекор 8 — Врати го DOI во репозиториумот
Прати ми го DOI-то. Ќе го додадам во `README.md` и `CITATION.cff`, ќе го пресметам манифестот повторно и ќе ти дадам ажурирани фајлови за еден нов commit. Кодот и верзијата не се менуваат.

---
`GITHUB ≠ VALIDATION · ZENODO ≠ VALIDATION · HASH ≠ SCIENTIFIC PROOF` — тие ја докажуваат идентичноста и достапноста на кодот. Тестовите и независната проверка го докажуваат однесувањето.
