# Forensics Report: v15 vs v17.2

## 1. Estatísticas de Score
```text
Metric                 v15        v17.2       Delta
----------------------------------------------------
Mean Score             $37704     $45158     $7454     
Median Score           $38810     $44438     $5628     
Std Dev                $6963      $15057     -
Min Score              $22404     $11298     -
Max Score              $47840     $78161     -
Win Rate (vs starter)  100%       100%       -
Win Rate (v17 vs v15)  -          15/20        -
```

## 2. Produção e Economia
```text
Metric                 v15        v17.2       Delta
----------------------------------------------------
Sell Revenue           $1143425   $1473370   $329945   
Total Sells            15881      16801      920       
MILK                   2885       3040       155       
WOOL                   600        1674       1074      
FERTILIZER             3359       4393       1034      
WHEAT                  9037       7478       -1559     
STRAWBERRY             0          216        216       
MELON                  0          0          0         
```

## 3. Comportamentais (Ações emitidas pelo Dispatcher)
```text
Metric                 v15        v17.2       Delta
----------------------------------------------------
PASS %                 30.8     % 5.6      %
FEED                   5496       6344       848       
WATER                  0          908        908       
CARE                   3647       4589       942       
PLANT                  0          1588       1588      
HARVEST                2110       10458      8348      
```

## 4. State Integrity Layer (v17.2 Telemetry)
```text
invalid_action_intercepted     2740
feed_precondition_fail         2363
place_precondition_fail        0
plant_precondition_fail        0
water_precondition_fail        0
care_precondition_fail         0
circuit_breaker_triggered      3605
replan_count                   3605
max_consecutive_same_intent    14
```

## 5. Dinâmica do Rebanho
```text
Metric                 v15        v17.2
----------------------------------------------------
Final COW              7          11        
Final SHEEP            1          2         
Survival Rate          2.5      % 4.1      %
Collapse Events        0          0         
```

## 6. Distribuição dos Deltas (v17.2 vs v15)
```text
Seed 42: v17.2=$  59740 | v15=$  38940 | Delta=$  +20800 (+53.4%)
Seed 43: v17.2=$  11298 | v15=$  47840 | Delta=$  -36542 (-76.4%)
Seed 44: v17.2=$  67648 | v15=$  22404 | Delta=$  +45244 (+201.9%)
Seed 45: v17.2=$  48664 | v15=$  43233 | Delta=$   +5431 (+12.6%)
Seed 46: v17.2=$  78161 | v15=$  42298 | Delta=$  +35863 (+84.8%)
Seed 47: v17.2=$  45329 | v15=$  39721 | Delta=$   +5608 (+14.1%)
Seed 48: v17.2=$  37170 | v15=$  30905 | Delta=$   +6265 (+20.3%)
Seed 49: v17.2=$  59138 | v15=$  38679 | Delta=$  +20459 (+52.9%)
Seed 50: v17.2=$  44486 | v15=$  35016 | Delta=$   +9470 (+27.0%)
Seed 51: v17.2=$  37101 | v15=$  38652 | Delta=$   -1551 ( -4.0%)
Seed 52: v17.2=$  53583 | v15=$  44556 | Delta=$   +9027 (+20.3%)
Seed 53: v17.2=$  35416 | v15=$  43595 | Delta=$   -8179 (-18.8%)
Seed 54: v17.2=$  21705 | v15=$  42870 | Delta=$  -21165 (-49.4%)
Seed 55: v17.2=$  39786 | v15=$  32667 | Delta=$   +7119 (+21.8%)
Seed 56: v17.2=$  29998 | v15=$  23051 | Delta=$   +6947 (+30.1%)
Seed 57: v17.2=$  36719 | v15=$  45845 | Delta=$   -9126 (-19.9%)
Seed 58: v17.2=$  44390 | v15=$  42069 | Delta=$   +2321 ( +5.5%)
Seed 59: v17.2=$  43339 | v15=$  38414 | Delta=$   +4925 (+12.8%)
Seed 60: v17.2=$  56928 | v15=$  34206 | Delta=$  +22722 (+66.4%)
Seed 61: v17.2=$  52567 | v15=$  29116 | Delta=$  +23451 (+80.5%)
```
