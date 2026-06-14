# Backlog — Torneios e Melhorias 🚀

> **Nota:** os dois itens originais deste arquivo já foram **CONCLUÍDOS** (v2/v3). Mantido
> como histórico + backlog atual. Roadmap consolidado em [AI_HANDOFF.md](AI_HANDOFF.md) §11.

---

## ✅ Concluído

### 1. Dicionário detalhado dos Grand Slams — FEITO
Ficha completa de cada Slam (local, superfície, fundação, premiação, maior campeão/campeã,
história) em `tennis_data.json`. Diferenciação inteligente: "me fala sobre wimbledon" → detalhes;
"quem ganhou wimbledon" → campeões. Método `get_grand_slam_details()` em `engine.py`.

### 2. Lista de todos os torneios da ATP (calendário) — FEITO
18 torneios em `tournament_details`: 9 Masters 1000 (Indian Wells, Miami, Monte Carlo, Madrid,
Roma, Canadá, Cincinnati, Shanghai, Paris), 8 ATP 500 (Rio Open, Barcelona, Queen's, Halle,
Acapulco, Dubai, Basileia, Viena) e o ATP Finals (Turim). Listagem via `get_tournaments_list()`;
explicação de pontos/prestígio por categoria coberta pela `knowledge_base.json`.

---

## 🔜 Backlog atual

1. **RAG vetorial** (embeddings) no lugar do *grounding* por keyword — ver [LLM_HYBRID.md](LLM_HYBRID.md).
2. **Head-to-Head** entre jogadores (confrontos diretos).
3. **Estatísticas avançadas**: aces, % 1º serviço, duplas faltas por jogador.
4. **Cache de respostas do LLM** + avaliação automática de alucinação.
5. **Mais jogadores/lendas** fora do Top 100.
6. **Calendário completo** com datas e locais (ATP/WTA 250/500/1000/Finals).
