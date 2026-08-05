# 🚜 Manual de Regras e Prioridades do Agente (Kaggriculture)

Este documento define a Árvore de Decisão e as regras de negócio que o agente autônomo deve seguir a cada turno da simulação.

---

## 💰 1. Regras de Mercado e Galpão (Shed)
Antes de realizar qualquer ação no campo, o agente deve organizar as finanças e o inventário.

*   **Regra 1.1 - Prevenção de Overflow:** O limite de segurança do galpão é de **75 itens**. Se o inventário total ultrapassar esse limite, o agente entra em modo de liquidação e vende o excesso.
*   **Regra 1.2 - Venda Inteligente:** Produtos com quantidade superior a 5 unidades devem ser vendidos (50% do estoque se o galpão estiver seguro; 100% do excedente se estiver lotado).
*   **Regra 1.3 - Compras Ativas:** Se o saldo em moedas (coins) for superior a 400:
    *   Comprar sementes de **Melão** (alto valor).
    *   Comprar sementes de **Trigo** (essencial para alimentar animais).

---

## 👨‍🌾 2. Prioridades de Ação no Campo (Por Peão/Fazendeiro)
Para cada unidade (peão) disponível no turno, o agente deve avaliar o bloco (tile) em que ele se encontra e executar a **primeira ação válida** seguindo a ordem de prioridade abaixo:

1.  **Colheita Imediata (`HARVEST`):** 
    *   *Condição:* A planta no bloco atual terminou de crescer (`is_ready_to_harvest`).
    *   *Motivo:* Liberar espaço e gerar produtos para venda.
2.  **Bem-Estar Animal (`FEED` / `HARVEST`):**
    *   *Condição:* Existe um animal no bloco.
    *   *Ação A:* Se não foi alimentado hoje (`!fed_today`), executar `FEED` (requer Trigo no inventário).
    *   *Ação B:* Se o animal está pronto para produzir (`ready_to_produce`), executar `HARVEST`.
    *   *Motivo:* Evitar que animais fujam por fome e coletar recursos valiosos.
3.  **Irrigação Obrigatória (`WATER`):**
    *   *Condição:* Existe uma planta e ela não foi regada hoje (`!watered_today`).
    *   *Motivo:* Plantas não regadas atrasam o crescimento e podem morrer.
4.  **Maximização de Lucro (`FERTILIZE`):**
    *   *Condição:* Existe uma planta, não foi fertilizada recentemente (`!fertilized_recently`) e há fertilizante no inventário.
    *   *Motivo:* Dobrar o rendimento da colheita (especialmente útil para Melões).
5.  **Limpeza de Terreno (`DIG`):**
    *   *Condição:* O bloco contém mato/ervas daninhas (`has_weed`).
    *   *Motivo:* Preparar o solo para o plantio no próximo turno.
6.  **Plantio Estratégico (`PLANT`):**
    *   *Condição:* O bloco está completamente vazio (sem planta, sem mato, sem estrutura).
    *   *Ação:* Seguir as **Regras de Rotação de Culturas** (Secção 3).
7.  **Inação (`PASS`):**
    *   *Condição:* Nenhuma das condições acima for atendida.

---

## 🌱 3. Regras de Rotação de Culturas (Plantio)
Quando o agente decide plantar, ele deve escolher a semente com base no ciclo de dias para balancear lucro e sustentabilidade:

*   **Dias múltiplos de 3 (Foco em Lucro):** Plantar **Melão** (`PLANT MELON`). Ciclo longo, mas maior retorno financeiro.
*   **Dias múltiplos de 2 (Foco em Sustento):** Plantar **Trigo** (`PLANT WHEAT`). Ciclo médio, essencial para manter a regra de Bem-Estar Animal.
*   **Dias restantes (Foco Rápido/Fallback):** Plantar **Cenoura** (`PLANT CARROT`). Ciclo rápido, baixo custo, gera fluxo de caixa imediato.