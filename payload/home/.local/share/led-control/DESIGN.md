# Design
Controle operacional em português, integrado à bandeja existente do KDE.
O clique no círculo abre um popover de 344 px, abaixo da barra superior,
sem moldura de janela. Repetir o clique recolhe. Qt::Popup oferece fechamento
por Escape e clique fora. A aplicação usa XWayland para posicionar o popup
pelos limites da bandeja obtidos do Plasma; a posição do cursor é usada quando
está sobre a bandeja. A implementação recorre ao monitor disponível e limita
as bordas da tela.

Superfície escura #222732, controles #363e4e, texto #f3f5fa, contorno #50596b.
Fonte SF Pro Text, corpo13 px regular, título16 px semibold, kerning ligado
e espaçamento entre letras0,15 px (0,1 px no título). Espaçamento12 px e margens20 px.
Oito amostras de cor em duas linhas; nomes em tooltip e rótulo acessível.
Cor atual, brilho e estado da aplicação permanecem visíveis. Inventário e
início automático ficam na seção expansível Opções e dispositivos.

O painel Flex Hub preserva o tema XMacTahoe e os comandos existentes.
Cartões translúcidos claros a12%, raio16 px, colunas86 px, ícones22 px.
Rótulos compactos em português e estado vazio explícito para mídia.

No Flex Hub, textos principais13 px e peso médio, rótulos pequenos12 px
regulares, kerning ligado e espaçamento entre letras0,15 px.
