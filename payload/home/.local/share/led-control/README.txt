Cores dos LEDs

Clique no círculo colorido da bandeja na barra superior para abrir o popover
compacto, posicionado abaixo do ícone. Clique novamente para recolher.
O menu de contexto oferece cores rápidas e seletor personalizado.
Pronto, Escape ou clicar fora fecha o popover e mantém o app na bandeja.
Sair do controle, no menu do botão direito, encerra o app.
As cores rápidas têm nomes nos tooltips e rótulos de acessibilidade.
Opções e dispositivos expande o inventário e o início automático.
A última cor aplicada e o brilho são restaurados no próximo login.
O início automático pode ser desativado na janela.

Dispositivos: dois módulos Corsair Vengeance RGB Pro DDR4, Gigabyte RTX 3060,
Logitech G502, ASUS TUF B550M-PLUS, Nollie8 (8 canais de 126 endereços).
O header ARGB ASUS está configurado para 120 endereços. Isso cobre os LEDs
conectados até esse limite; endereços extras não representam LEDs físicos.

O software verifica o perfil final do OpenRGB e erros de escrita reportados.
A verificação não equivale a observar as luzes fisicamente.
LEDs de status sem RGB e telas USB não são controladores de cor compatíveis.

Arquivos:
  app: ~/.local/bin/led-control
  fonte: ~/.local/share/led-control/src/main.cpp
  preferências: ~/.config/Aleph/led-control.conf
  log da última aplicação: ~/.local/share/led-control/last-run.log
  perfil: ~/.config/OpenRGB/profiles/Aleph-LastApplied.json
  autostart: ~/.config/autostart/led-control.desktop

Compilar:
  g++ -std=c++17 -O2 src/main.cpp -o ~/.local/bin/led-control $(pkg-config --cflags --libs Qt6Widgets Qt6Network)

Backend oficial OpenRGB: https://openrgb.org/
Binário extraído do AppImage oficial do pipeline master, baixado em 2026-10-18.
O app e backend rodam como usuário comum. Regras udev dão acesso à sessão
ativa apenas aos controladores USB detectados e aos barramentos SMBus 0–2.
