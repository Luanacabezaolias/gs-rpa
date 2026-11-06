# Fluxo da automação (para o PDD / BPMN)

```mermaid
flowchart TD
    A([Início da rodada]) --> B[Buscar ocorrências na API]
    B -->|API fora do ar| X[3 tentativas com espera crescente] --> Y([Aborta e registra erro fatal])
    B --> C{Há ocorrências 'nova'?}
    C -->|Não| P
    C -->|Sim| D[/Para cada ocorrência nova, da mais antiga à mais recente/]
    D --> E{Duplicada? mesmo trecho + tipo, em até 60 min}
    E -->|Sim| F[Marca 'duplicada' e aponta a original] --> D
    E -->|Não| G{Trecho tem responsável?}
    G -->|Não| H[Registra aviso: ação manual] --> D
    G -->|Sim| I[Define prioridade: alta, média ou baixa]
    I --> J[Envia notificação]
    J -->|Falhou| K[Registra erro; permanece 'nova' para nova tentativa] --> D
    J -->|OK| L[Marca 'notificada' + data/hora] --> D
    D -->|fim do lote| P[/Para cada ocorrência notificada ou escalada/]
    P --> Q{Última inspeção mostra trecho livre?}
    Q -->|Sim| R[Marca 'resolvida'] --> P
    Q -->|Não| S{Prazo vencido?}
    S -->|Sim| T[Reenvia ao responsável e ao supervisor; marca 'escalada'] --> P
    S -->|Não| P
    P -->|fim do lote| Z([Resumo da rodada no log])
```

Prazos por prioridade: alta 30 min, média 120 min, baixa 480 min.
Para entregar em BPMN: redesenhe este fluxo em https://demo.bpmn.io (ou Bizagi) e exporte a imagem.
