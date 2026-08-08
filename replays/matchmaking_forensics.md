# Kaggriculture — Matchmaking Forensics

**N partidas:** 9 | **N jogadores:** 9

## 1. Quem está ganhando?

### 1. SiddarthNayak50 (Score: $59,326)
- **Receita:** $64,438
- **Animais:** 0 Vacas, 0 Ovelhas
- **Crops Principais (Plantios):** CARROT(117), WHEAT(85), MELON(32)
- **Vendas Principais:** CARROT(252), WHEAT(220), MELON(180)
- **Eficiência:** 4438 passos. $14.52 por movimento.

### 2. those how (Score: $50,500)
- **Receita:** $48,309
- **Animais:** 0 Vacas, 0 Ovelhas
- **Crops Principais (Plantios):** MELON(58)
- **Vendas Principais:** MELON(278)
- **Eficiência:** 3154 passos. $15.32 por movimento.

### 3. t3l3k3n3sis (Score: $49,880)
- **Receita:** $59,567
- **Animais:** 0 Vacas, 0 Ovelhas
- **Crops Principais (Plantios):** MELON(34), STRAWBERRY(28)
- **Vendas Principais:** MELON(165), STRAWBERRY(109)
- **Eficiência:** 3626 passos. $16.43 por movimento.

### 4. Rilen T. L. (Score: $42,665)
- **Receita:** $80,173
- **Animais:** 7 Vacas, 1 Ovelhas
- **Crops Principais (Plantios):** 
- **Vendas Principais:** WHEAT(434), FERTILIZER(158), MILK(133)
- **Eficiência:** 3473 passos. $23.08 por movimento.

### 5. JoJa (Score: $41,700)
- **Receita:** $58,752
- **Animais:** 6 Vacas, 4 Ovelhas
- **Crops Principais (Plantios):** WHEAT(139), MELON(11), CARROT(7)
- **Vendas Principais:** WHEAT(170), FERTILIZER(129), MILK(99)
- **Eficiência:** 3521 passos. $16.69 por movimento.

## 2. Como os vencedores ganham?
Os 3 melhores jogadores do dataset (SiddarthNayak50, those how, t3l3k3n3sis) adotam uma estratégia **100% Agrícola (CROP-HEAVY)**. Eles possuem **Zero Vacas e Zero Ovelhas**. Eles geram receita vendendo MELON, CARROT e STRAWBERRY em alto volume, capitalizando em sementes caras e colheitas lucrativas sem imobilizar capital em pastos.

## 3. Qual é o verdadeiro animal flywheel?
Nos oponentes, o único que adotou um modelo de animais forte foi **JoJa** (Score: $41.7k). Ele terminou com 6 Vacas e 4 Ovelhas. A estratégia parece ser híbrida: vende WHEAT, FERTILIZER e MILK. Mas a estratégia pure crop comercial (SiddarthNayak50 com $59k) os superou com larga vantagem.

## 4. Qual é o papel real do WHEAT?
Jogadores PURE CROP usam WHEAT primariamente comercial ou misturado com outras culturas para giro de caixa inicial. SiddarthNayak50 plantou 85 WHEAT e vendeu 220 WHEAT, indicando uso 100% comercial sem alimentar animais.

## 5. STRAWBERRY e MELON são relevantes?
**Extremamente relevantes.** O Top 1 usa CARROT e MELON. O Top 2 usa MELON puro. O Top 3 usa MELON e STRAWBERRY. Essas culturas estão dominando as partidas acima de $49k e compõem mais de 90% da receita.

## 6. Eficiência Espacial e Movimento
O Top 1 gera receita massiva (cerca de $10 por passo) porque os trabalhadores apenas plantam, regam e colhem (HARVEST), não precisando buscar WHEAT no celeiro para alimentar vacas a cada ciclo.

## 7. Como o v17.2 se compara aos melhores? (Laboratório vs Matchmaking)

| Dimensão | v17.2 (Lab Avg) | SiddarthNayak50 (Top 1) | those how (Top 2) | t3l3k3n3sis (Top 3) |
|---|---|---|---|---|
| Score | $45158 | $59,326 | $50,500 | $49,880 |
| Revenue | $73668 | $64438 | $48309 | $59567 |
| Final Cows | 11 | 0 | 0 | 0 |
| MELON (sold) | 0 | 180 | 278 | 165 |
| STRAWBERRY (sold) | 10 | 0 | 0 | 109 |
| WHEAT (sold) | 373 | 220 | 0 | 0 |
| Movement Steps | 45000 | 4438 | 3154 | 3626 |

## 8. Descoberta de Oportunidades
### P0 - CROP HEAVY DOMINANCE
O v17.2 trava muito capital na compra de 11 vacas e perde tempo se movendo massivamente (FEED/CARE) enquanto os adversários reais usam os primeiros dias para migrar todo o capital para **MELON e STRAWBERRY**. Culturas de alto valor agregado sem tempo gasto buscando trigo provaram render quase $60k no matchmaking real.

**Recomendação Experimental:** Oportunidade de criar uma mutação (CROP HEAVY) no laboratório, utilizando MELON/STRAWBERRY, mas alicerçada na nossa infraestrutura State Integrity e Pathing BFS provada, possivelmente superando os $60k.
