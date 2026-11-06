# Roteiro do vídeo (até 3 minutos)

O enunciado pede exatamente 3 coisas: **(1)** problema e papel da automação, **(2)** execução de ponta a ponta na prática, **(3)** regra de decisão, integração com o MVP e tratamento de falhas.

| Tempo | O que mostrar | O que falar (adapte com suas palavras) |
|---|---|---|
| 0:00 – 0:25 | Slide ou README com o nome AccessFlow | "Clínicas têm passagens acessíveis bloqueadas por caixas e carrinhos. A visão e o robô detectam, mas alguém precisa agir. A minha automação transforma a detecção em ação: registra, evita duplicidade, avisa o responsável e confirma a resolução." |
| 0:25 – 0:50 | Fluxo (docs/fluxo.md ou BPMN) | Explique o caminho: nova → duplicada ou notificada → resolvida ou escalada. |
| 0:50 – 1:50 | Terminal: `python -m mock_api.server` (ou a API real) e `python -m src.automacao`. Mostre o log rodando e depois as ocorrências mudando de status | Aponte cada linha: "a 2 foi marcada duplicada da 1", "a 3 foi notificada com prioridade média", "a 7 foi resolvida porque a inspeção mostrou o trecho livre", "a 6 passou do prazo e foi escalada". |
| 1:50 – 2:20 | Painel do MVP (ou resposta da API) exibindo os status atualizados | "A automação escreve na mesma API que o painel lê, por isso a mudança aparece aqui." Esta é a **integração com o MVP**. |
| 2:20 – 2:50 | Falhas: (a) ocorrência 4 sem responsável, (b) ocorrência 5 com e-mail inválido, (c) derrubar a API e mostrar as 3 tentativas e o aborto | "Nenhuma falha é silenciosa: tudo vai para o log, e um item com erro não derruba o lote." |
| 2:50 – 3:00 | `python -m pytest` com 19 testes passando | Fechamento: LGPD (e-mails mascarados no log, dados fictícios) e link do repositório. |

## Checklist antes de gravar
- [ ] Aparecer a regra de decisão funcionando (duplicidade, prioridade, prazo)
- [ ] Aparecer a integração com o MVP (API real, não só a simulada)
- [ ] Mostrar pelo menos uma falha tratada
- [ ] Máximo de 3 minutos, link público e testado em janela anônima
- [ ] Nenhum e-mail ou dado pessoal real visível na tela
