---
title: "黄金トネッツを触ろう（Golden Tonnetz、実験モード）"
emoji: "🌟"
type: "idea"
topics: ["webaudio", "javascript", "音楽", "シンセ", "ブラウザ"]
published: false
---

## 黄金トネッツとは

[Puntone](https://puntone-synth.pages.dev/) の実験モードのひとつ、**黄金トネッツ（Golden Tonnetz）**を掘り下げる記事です。全モードの一覧や基本操作は「Puntone 操作ガイド」、通常の（三角格子の）トネッツについては「トネッツで演奏しよう」を参照してください。

黄金トネッツは、東京大学の今井悠介氏の論文 [*Golden Tonnetz*（arXiv:2509.21428）](https://arxiv.org/abs/2509.21428) にヒントを得たモードです。論文では、正五角形の対角線が作る五芒星、そして五芒星が含む黄金比を持つ三角形を使って、**音楽理論でおなじみのトネッツ**（音の格子図）を拡張しています。Puntoneではこの黄金トネッツを実際に演奏できる鍵盤として実装しました。

![黄金トネッツの盤面](/images/puntone-golden-tonnetz-guide/golden-tonnetz-board.png)

## 1. 論文の着想: 黄金三角形とグノモン

まず論文のアイデアを紹介します。（誤読がありましたらコメントお願いします）
**黄金三角形**は「脚:底辺 = φ:1（φは黄金比、約1.618）」の鋭角二等辺三角形、**黄金グノモン**は同じ比率の鈍角二等辺三角形です。

![黄金三角形とグノモン](/images/puntone-golden-tonnetz-guide/golden-triangle-gnomon.png)

論文は、この2種類の三角形の上にうまく7音を配置すると、次の2つが同時に成り立つことを示しました。

- 全音階（ダイアトニックスケール）を音の高さ順に並べた輪（例: C→D→E→F→G→A→B→C）が、そのまま三角形の辺をたどる一筆書きの経路になる
- その音階の主要三和音（I・III・IV・V・VI度）が、三角形の中の小さな黄金三角形／グノモンとしてちょうど現れる

長調はこの黄金三角形（鋭角）で、短調はグノモン（鈍角）で表せます。この「1つの調＝1枚の三角形」を上下左右にどこまでも敷き詰めていくと、五度上がるごとに横へ、半音上がるごとに縦へ進む無限格子ができあがります。これが論文の言う黄金トネッツです。隣り合う三角形は、5度違いの同じ旋法どうしなら4音、同主調の長調⇔短調なら2音、半音違いの長調⇔短調なら1音を共有しながらつながっています。

## 2. コードを弾く: 三角形とグノモンを探す

指で円を通過するようになぞることで、演奏ができます。
（円を通過 or指を離すタイミングで発音します）
マルチタッチにも対応しています。

盤面には音数が多いため、後述の調ノブで絞り込むとよいかもです。
ここに、Cメジャースケールのみの図を示します。

![盤面の一部（Cメジャースケールの音のみ）](/images/puntone-golden-tonnetz-guide/golden-tonnetz-pool-keyfilter.png =240x)

また、コードを弾く際には、下記のような黄金三角形・黄金グノモン、その他の図形を探すことでコードを弾くことができます。
「※」が付いたコードは、この図に写っている範囲外の音を含みます。

| コード | 例 || コード | 例 || コード | 例 |
|---|---|---|---|---|---|---|---|
| maj | ![](/images/puntone-golden-tonnetz-guide/chord-Cmaj-paper.png =120x) || sus2※ | ![](/images/puntone-golden-tonnetz-guide/chord-Csus2-paper.png =120x) || m7b5※ | ![](/images/puntone-golden-tonnetz-guide/chord-Bm7b5-paper.png =120x) |
| min | ![](/images/puntone-golden-tonnetz-guide/chord-Emin-paper.png =120x) || maj7 | ![](/images/puntone-golden-tonnetz-guide/chord-Cmaj7-paper.png =120x) || 6 | ![](/images/puntone-golden-tonnetz-guide/chord-C6-paper.png =120x) |
| dim※ | ![](/images/puntone-golden-tonnetz-guide/chord-Bdim-paper.png =120x) || m7※ | ![](/images/puntone-golden-tonnetz-guide/chord-Dm7-paper.png =120x) || m6※ | ![](/images/puntone-golden-tonnetz-guide/chord-Dm6-paper.png =120x) |
| sus4 | ![](/images/puntone-golden-tonnetz-guide/chord-Esus4-paper.png =120x) || 7※ | ![](/images/puntone-golden-tonnetz-guide/chord-G7-paper.png =120x) || | |

## 3. 調ノブ

盤面を特定の調に絞り込む機能です。ONにすると選んだ調の長音階に含まれない音が暗くなり、鳴らせなくなります。

![Cメジャーに絞り込んだ状態](/images/puntone-golden-tonnetz-guide/golden-tonnetz-keyfilter.png)

盤面全体が5000個以上のノードを持つ広い格子なので、最初は音を探すのが大変に感じるかもしれません。調ノブでハ長調などに絞ると、迷わず演奏しやすくなります。

## 4. 律ノブとアップロード音源

ノブ列の**律**では、平均律／純正律／ピタゴラス音律を切り替えられます（既存トネッツと同じ3択）。既定は純正律です。

音源ボタンからは、プリセットの倍音のほか、自前の音声ファイルのアップロードやその場での録音も使えます。使い方はカタライザーモードと共通です。詳しくは「Puntoneカタライザーガイド」を参照してください。

## まとめ

トネッツと異なり、長調・短調を表現できる点が優秀な盤面でした。
一方で、盤面上の音数が多く、コードを弾く際には少々やりづらいところもありそうです。
個人的には盤面がきれいで好きです。

👉 [黄金トネッツを触る](https://puntone-synth.pages.dev/idea.html?polyMode=golden-tonnetz)

## 応援・フィードバック

- ☕ [開発者を応援する](https://buy.stripe.com/4gM3cwgo7cQs6RsatZbsc03)
- 📝 [ご意見・ご要望を送る](https://forms.gle/3UNMJufgTk43Fhip7)
