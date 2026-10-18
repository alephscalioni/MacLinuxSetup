# MacLinux Setup

Snapshot local e aplicador dos ajustes feitos no Fedora 44 com KDE Plasma e base XMacTahoe. Reaplica a configuração em um comando e salva um backup antes de alterar arquivos.

## Um comando

```sh
maclinux-aplicar
```

Ou clique em **Aplicar ajustes macOS**, no menu de aplicativos ou na área de trabalho.

A execução reaplica os arquivos, recarrega o desktop e inicia o controle dos LEDs. Se o Chrome ainda usar a própria moldura, ele é encerrado normalmente, recebe a configuração de decoração do sistema e reabre com a última sessão. Quando a configuração já está correta, o navegador permanece aberto.

## O que foi salvo

- Temas Aurorae claro e escuro com os botões macOS e geometria corrigida: laterais e base sem borda pintada, padding inferior de 86 px e margem inferior do título de 4 px.
- Configurações selecionadas do KWin, incluindo cantos arredondados e decoração Aurorae.
- Flex Hub corrigido, seus controles, rótulos e tipografia.
- Temas GTK locais e quatro pesos da fonte SF Pro Text usados na configuração.
- App dos LEDs, fonte C++, backend OpenRGB extraído, configuração de canais e última cor/brilho.
- Histórico Git do LedLinux em `LedLinux.bundle`.
- Regras udev RGB restritas aos dispositivos e barramentos configurados.
- Ajuste do Chrome para usar a decoração do sistema.

O snapshot é privado e específico deste computador. Inclui arquivos de terceiros, fontes de uso local e identificadores do hardware. Esses componentes mantêm suas licenças originais. Credenciais do GitHub, cookies, histórico, sessões e dados de conta do Chrome não são incluídos.

## Restaurar em outra pasta ou após reinstalar

Requer Fedora 44 x86_64, KDE Plasma, base XMacTahoe instalada e as bibliotecas Qt 6 utilizadas pelo controle RGB. Esse pacote não instala o sistema operacional nem a base completa do XMacTahoe.

```sh
gh repo clone alephscalioni/MacLinuxSetup "$HOME/Projetos/desktop-macos-aplicador"
cd "$HOME/Projetos/desktop-macos-aplicador"
./aplicar
```

O repositório é privado: o GitHub CLI precisa estar autenticado. O comando `./aplicar` executa a aplicação e instala o atalho/comando automaticamente. `install-launcher.py` também pode instalar apenas o atalho, sem aplicar os ajustes. Se as regras de acesso aos LEDs estiverem ausentes, o sistema solicita autenticação de administrador por `pkexec`. No computador já configurado, não é necessário instalá-las novamente.

## Conferir sem alterar

```sh
./aplicar --dry-run
```

## Desfazer

Os backups ficam em `~/.local/state/maclinux-aplicador/backups/`. O caminho exato aparece no início da execução.

```sh
maclinux-aplicar --restore-latest
# ou
maclinux-aplicar --restore /caminho/do/backup
```

O rollback restaura os arquivos locais afetados e somente a preferência alterada do Chrome, preservando suas outras configurações. Regras de sistema instaladas ficam com backup em `/var/lib/maclinux-aplicador/` e exigem administrador para restaurar. O rollback não desinstala essas regras automaticamente.

## Limites do RGB

A versão salva do LedLinux valida dois módulos Corsair, RTX 3060, G502, ASUS TUF B550M-PLUS e Nollie8. Outros controladores exigem adaptação. A cor restaurada é a última capturada no snapshot. Um perfil validado confirma o estado do software, não uma leitura física das luzes.

## Verificação

```sh
/usr/bin/python3 -m unittest -v test_apply.py
```

Os testes usam uma pasta temporária: validam aplicação e rollback, preservação das outras preferências do Chrome, links e caminhos, sem controlar a sessão real.
