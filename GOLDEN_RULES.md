# Regras de Ouro — Kaggriculture

Conhecimento validado por experimentação local (env `kaggle-environments`) e
estudo de oponentes reais (replays baixados via Kaggle CLI). Objetivo: NÃO
repetir erros que custaram o rating 70.4 e subir o teto de moedas de forma
confiável.

## 1. Melão é o motor de dinheiro confiável
- Maior valor por tile: base $250, colheita de até 6 unidades = ~$1.500 por
  tile por ciclo (one-time, 10 dias de crescimento).
- Volume minúsculo (≈108 melões/season) perto de I₀=10.000 (T=300) → o preço
  SÓ cai de verdade se você despejar centenas de melões de uma vez. Venda com
  teto (≤15/turno) e o mercado fica perto do preço base.
- **Maximize o número de tiles de MELÃO** dentro do orçamento de tiles.

## 2. Fazenda DENSA em 2 quadrants vence espalhar em 4
- Custo de viagem das unidades anula o ganho de tiles extras. Validado:
  - 2 quadrants (50 tiles) + ~8 mãos  → ~6.000 moedas média
  - expansão p/ 3º/4º quadrant          → ~3.900 moedas média (REGRESSÃO)
- Comprar só o NE (quads 1→2). NÃO comprar SW/SE.

## 3. Motor de ANIMAIS é passivo de volatilidade, não ativo
- Gansos/vacas morrem em spiral: comprar $300 → colocar → não ser alimentado
  2 dias → fugir (irrecuperável) → recomprar. Cada morte = prejuízo + perda de
  produção.
- Sintoma observado: 11 currais construídos, só ~5 gansos preenchidos → tiles
  desperdiçados que poderiam ser MELÕES.
- Leite/lã DESPENcam com glut (above_target 1.6 / 3.2 → $1). Ovos são estáveis
  (above_target 0.20 → ~$40). Se usar animais, foque em GANSOS + alimentação
  bulletproof; caso contrário, DROPE o motor de animais e vá 100% plantação.

## 4. Mão de obra contratada é BARATA e essencial
- Custo fib: 1,1,2,3,5,8… zera todo dia. Com 8 unidades × 24 turnos = 192
  ações/dia por um custo irrisório.
- **Nunca deixe a mão de obra colapsar**: com 1 fazendeiro só, a fazenda não é
  mantida (plantas viram mato, animais fogem) → colapso total.
- Teto de mãos: `4 + min(4, day//5)` (até 8). Mais que isso (5+min(5,day//4)=10)
  REGREDEU (~7.700 vs ~9.000).

## 5. Mercado: venda consciente evita crashes
- Ovos: venda tudo (estável).
- Leite/lã/melão/morango: cap por turno (≤15-20) + piso de preço; liquidação
  total no fim (day ≥ 27).
- Cuidado ao despejar premium: o preço cai com glut e vira $1.

## 6. Confiabilidade > complexidade
- Um bot simples de melão (PASS 685/720, 3 melões) marcou 5.549 e venceu um
  agente complexo de 5.105. Floor alto ganha rating (vitórias); teto sem chão
  perde pontos.
- Corra atrás do bug que causa colapso ANTES de adicionar features.

## 7. Armadilhas já pisadas (NÃO repetir)
- **Hire-buffer de 150**: quando o dinheiro caiu p/ 140, a contratação parou, a
  fazenda colapsou → rating 70.4. Buffer deve ser ~20.
- **Plantar só quando "por acaso" está num tile vazio**: o agente vagava e não
  construía plantava nada. Tem que navegar ATIVAMENTE até tiles vazios.
- **wheat_target acoplado a animais frágeis**: impedia melão/morango de serem
  plantados. Plante culturas em paralelo (mais deficitário primeiro).
- **Alimentar abaixo de regar na prioridade**: animal morre em 2 faltas (= $300
  de perda). Alimentar é crítico de morte, vai antes de regar.
