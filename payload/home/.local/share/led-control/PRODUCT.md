# Controle de LEDs
<!-- impeccable:product-schema 1 -->
## Platform
Native Linux / KDE Plasma.
## Stack
Qt 6 Widgets, C++, OpenRGB. App nativo confirmado pelo usuário.
## Users
Aleph, ajustando a iluminação do próprio computador pela barra superior.
## Product Purpose
Aplicar azul a todos os dispositivos RGB compatíveis e permitir troca de cor.
## Operating Context
Fedora 44, KDE Plasma Wayland, painel superior com bandeja do sistema.
## Capabilities and Constraints
Cores rápidas, seletor de cor, início automático e restauração da última cor confirmados pelo usuário. Acesso ao hardware precisa de regras udev. Compatibilidade depende de detecção real do OpenRGB. Inventário final: dois módulos Corsair Vengeance RGB Pro DDR4, RTX 3060, Logitech G502, ASUS TUF B550M-PLUS e Nollie8.

## Interaction refinement
O usuário pediu abertura junto à barra superior e melhoria do painel de controles. O app abre como popover compacto; inventário e início automático ficam em seção expansível.
