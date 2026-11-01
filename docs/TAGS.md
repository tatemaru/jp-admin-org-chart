# タグ一覧（見返し用）

時点の組織図を見るときは、コミットログより **タグで checkout** するのが簡単です。

## 使い方

```bash
git tag -l 'era/*'          # 時代の入口
git tag -l 'point/*'        # 主要イベント
git checkout point/2001-01-06-reorg
git checkout era/heisei-reorg
```

ブラウザでは [組織図ビューア](https://tatemaru.github.io/jp-admin-org-chart/viewer/) のセレクトボックスでも同じタグを選べます（`d3-org-chart`）。

GitHub なら Releases/Tags、またはコミット履歴のタグ印からも飛べます。

## 命名

| 種類 | 形式 | 用途 |
|------|------|------|
| `era/*` | `era/dajokan` など | 体制の切れ目（ざっくり移動） |
| `point/YYYY-MM-DD-*` | 施行日 + 短い英字 | 個別イベント（正確な時点） |
| `snapshot/YYYY-MM-DD` | 行政機構図の基準日 | 年次追従（法令イベントではない） |

`point/` と `snapshot/` の日付は **施行日／基準日**（コミット本文の `施行:` と同じ）。Git の AuthorDate が 1970-01-02 に寄っている明治のコミットでも、タグ名では本当の日付を使います。

## era（入口）

| タグ | 意味 |
|------|------|
| `era/dajokan` | 太政官制（政体書）以降 |
| `era/cabinet` | 内閣制度以降 |
| `era/empire` | 帝国議会以降 |
| `era/postwar` | 日本国憲法以降 |
| `era/heisei-pre-reorg` | 再編直前の1府22省庁 |
| `era/heisei-reorg` | 中央省庁再編以降（外局ディレクトリ開始） |
| `era/reiwa-detail` | デジタル庁以降（内部部局まで） |
| `era/current` | リポジトリ先端 |

## 主な point

`git tag -l 'point/*'` を参照。例:

- `point/1868-01-03-sanshoku`
- `point/1885-12-22-cabinet`
- `point/2001-01-06-reorg`
- `point/2021-09-01-digital`
- `point/2026-11-02-bosai`
