#include <QtWidgets>
#include <QLocalServer>
#include <QLocalSocket>

static QIcon swatch(QColor color) {
    QPixmap pix(32,32); pix.fill(Qt::transparent);
    QPainter p(&pix); p.setRenderHint(QPainter::Antialiasing);
    p.setPen(QPen(QColor("#f0f0f0"),2)); p.setBrush(color); p.drawEllipse(QRectF(5,5,22,22));
    return QIcon(pix);
}

int main(int argc, char **argv) {
    // XWayland permits exact tray anchoring for this small Qt popup.
    qputenv("QT_QPA_PLATFORM", "xcb");
    QApplication app(argc,argv);
    app.setApplicationName("led-control");
    app.setApplicationDisplayName("Cores dos LEDs");
    app.setOrganizationName("Aleph");
    app.setQuitOnLastWindowClosed(false);
    QFont textFont("SF Pro Text"); textFont.setPixelSize(13);
    textFont.setWeight(QFont::Normal); textFont.setKerning(true);
    textFont.setLetterSpacing(QFont::AbsoluteSpacing, 0.15);
    app.setFont(textFont);
    QString base=QDir::homePath()+"/.local/share/led-control";
    QLocalSocket existing; existing.connectToServer("aleph-led-control");
    if(existing.waitForConnected(250)) { existing.write("show"); existing.flush(); existing.waitForBytesWritten(250); return 0; }
    QLocalServer::removeServer("aleph-led-control");
    QLocalServer server; server.listen("aleph-led-control");
    QSettings settings;
    QColor current(settings.value("color","#0000ff").toString());
    if(!current.isValid()) current=QColor("#0000ff");
    QSystemTrayIcon tray(swatch(current));
    tray.setToolTip("Cores dos LEDs");
    QMenu menu;
    auto title=menu.addAction("Cores dos LEDs"); title->setEnabled(false);
    auto statusAction=menu.addAction("Preparando iluminação…"); statusAction->setEnabled(false);
    menu.addSeparator();
    QFrame window(nullptr, Qt::Popup | Qt::FramelessWindowHint);
    window.setObjectName("ledPopover"); window.setWindowTitle("Cores dos LEDs"); window.setFixedWidth(344);
    window.setStyleSheet("QFrame#ledPopover {background: #222732; border: 1px solid #50596b; border-radius: 16px;} QLabel {color: #f3f5fa;} QPushButton {padding: 8px 6px; border-radius: 8px; background: #363e4e; color: #f3f5fa; border: none;} QPushButton:hover {background: #46536a;} QPushButton:focus {border: 1px solid #8bbcff;} QCheckBox {color: #d6dce7;}");
    auto layout=new QVBoxLayout(&window); layout->setContentsMargins(20,20,20,20); layout->setSpacing(12);
    auto heading=new QLabel("Cores dos LEDs"); QFont f=heading->font(); f.setPixelSize(16); f.setWeight(QFont::DemiBold); f.setLetterSpacing(QFont::AbsoluteSpacing, 0.1); heading->setFont(f); layout->addWidget(heading);
    auto description=new QLabel("Iluminação sincronizada"); description->setWordWrap(true); layout->addWidget(description);
    auto preview=new QPushButton; preview->setMinimumHeight(38); layout->addWidget(preview);
    auto presets=new QGridLayout; presets->setSpacing(8); layout->addLayout(presets);
    auto custom=new QPushButton("Escolher outra cor…"); layout->addWidget(custom);
    auto brightnessLabel=new QLabel("Brilho"); layout->addWidget(brightnessLabel);
    auto brightness=new QSlider(Qt::Horizontal); brightness->setRange(0,100); brightness->setValue(settings.value("brightness",100).toInt()); brightness->setAccessibleName("Brilho dos LEDs"); layout->addWidget(brightness);
    auto status=new QLabel; status->setWordWrap(true); status->setTextInteractionFlags(Qt::TextSelectableByMouse); layout->addWidget(status);
    auto details=new QToolButton; details->setText("Opções e dispositivos"); details->setCheckable(true); details->setToolButtonStyle(Qt::ToolButtonTextBesideIcon); details->setArrowType(Qt::RightArrow); layout->addWidget(details);
    auto advanced=new QWidget; auto advancedLayout=new QVBoxLayout(advanced); advancedLayout->setContentsMargins(0,0,0,0); advancedLayout->setSpacing(10); advanced->hide(); layout->addWidget(advanced);
    auto devices=new QLabel; devices->setWordWrap(true); advancedLayout->addWidget(devices);
    QObject::connect(details,&QToolButton::toggled,[&](bool checked){ advanced->setVisible(checked); details->setArrowType(checked?Qt::DownArrow:Qt::RightArrow); window.adjustSize(); });
    auto startup=new QCheckBox("Iniciar ao entrar na sessão");
    QString autostart=QDir::homePath()+"/.config/autostart/led-control.desktop";
    startup->setChecked(QFile::exists(autostart)); advancedLayout->addWidget(startup);
    auto footer=new QHBoxLayout; auto retry=new QPushButton("Reaplicar"); auto hide=new QPushButton("Pronto"); footer->addWidget(retry); footer->addStretch(); footer->addWidget(hide); layout->addLayout(footer);
    QObject::connect(hide,&QPushButton::clicked,&window,&QWidget::hide);
    QObject::connect(startup,&QCheckBox::toggled,[&](bool enabled) {
        if(enabled) { QDir().mkpath(QFileInfo(autostart).absolutePath()); QFile::copy(base+"/led-control.desktop",autostart); }
        else QFile::remove(autostart);
        if(QFile::exists(autostart)!=enabled) { status->setText("Não foi possível alterar o início automático."); QSignalBlocker block(startup); startup->setChecked(QFile::exists(autostart)); }
    });
    QProcess process; process.setProcessChannelMode(QProcess::MergedChannels);
    QTimer timeout; timeout.setSingleShot(true); timeout.setInterval(45000);
    QObject::connect(&timeout,&QTimer::timeout,[&]{ process.kill(); });
    QColor pending=current, running=current; int pendingBrightness=brightness->value(), runningBrightness=pendingBrightness;
    bool queued=false;
    auto setStatus=[&](QString message){status->setText(message); statusAction->setText(message); tray.setToolTip("Cores dos LEDs\n"+message);};
    std::function<void()> launch;
    auto updatePreview=[&]{ preview->setIcon(swatch(pending)); preview->setText(pending.name().toUpper()+" · "+QString::number(pendingBrightness)+"%"); };
    launch=[&]{
        if(process.state()!=QProcess::NotRunning) { queued=true; return; }
        queued=false; running=pending; runningBrightness=pendingBrightness;
        QColor output(running.red()*runningBrightness/100,running.green()*runningBrightness/100,running.blue()*runningBrightness/100);
        QStringList args{"--noautoconnect"};
        for(auto name: {"Corsair Vengeance","Gigabyte GeForce","G502","ASUS TUF","Nollie 8CH"})
            args<<"--device"<<name<<"--mode"<<((QString(name)=="G502"||QString(name)=="ASUS TUF")?"Static":"Direct")<<"--color"<<output.name().mid(1);
        args<<"--save-profile"<<"Aleph-LastApplied";
        QFile::remove(QDir::homePath()+"/.config/OpenRGB/profiles/Aleph-LastApplied.json");
        setStatus("Aplicando cor…");
        process.start(base+"/vendor/squashfs-root/AppRun",args); timeout.start();
    };
    QObject::connect(&process,&QProcess::errorOccurred,[&](QProcess::ProcessError error){
        if(error==QProcess::FailedToStart) { timeout.stop(); setStatus("Não foi possível abrir o controle RGB. Veja o diagnóstico."); }
    });
    QObject::connect(&process,qOverload<int,QProcess::ExitStatus>(&QProcess::finished),[&](int code,QProcess::ExitStatus exitStatus){
        timeout.stop(); QString output=QString::fromUtf8(process.readAll());
        QFile log(base+"/last-run.log"); if(log.open(QIODevice::WriteOnly)) log.write(output.toUtf8());
        QStringList names;
        bool failed=code!=0||exitStatus!=QProcess::NormalExit;
        QFile profile(QDir::homePath()+"/.config/OpenRGB/profiles/Aleph-LastApplied.json");
        if(!profile.open(QIODevice::ReadOnly)) failed=true;
        const auto controllers=QJsonDocument::fromJson(profile.readAll()).object().value("controllers").toArray();
        const int expectedColor=(running.red()*runningBrightness/100)|((running.green()*runningBrightness/100)<<8)|((running.blue()*runningBrightness/100)<<16);
        for(auto value:controllers) {
            auto controller=value.toObject(); names<<controller.value("name").toString();
            auto modes=controller.value("modes").toArray();
            int active=controller.value("active_mode").toInt(-1);
            if(active<0||active>=modes.size()) { failed=true; continue; }
            auto mode=modes[active].toObject();
            auto colors=(mode.value("color_mode").toInt()==2?mode.value("colors"):controller.value("colors")).toArray();
            if(colors.isEmpty()) failed=true;
            for(auto color:colors) if(color.toInt(-1)!=expectedColor) failed=true;
        }
        for(auto expected:{"Gigabyte GeForce RTX 3060 Gaming OC","G502 LIGHTSPEED Wireless Gaming Mouse","ASUS TUF GAMING B550M-PLUS","Nollie 8CH"})
            if(!names.contains(expected)) failed=true;
        if(names.count("Corsair Vengeance RGB Pro DDR4")!=2) failed=true;
        devices->setText(names.isEmpty()?"Nenhum dispositivo RGB confirmado.":"Dispositivos detectados:\n"+names.join("\n"));
        QRegularExpression errors("error|failed|failure|cannot|could not|out of range|not found|wrong number",QRegularExpression::CaseInsensitiveOption);
        if(errors.match(output).hasMatch()) failed=true;
        if(failed) { setStatus("Falha ao aplicar. Abra o diagnóstico e tente reaplicar."); tray.showMessage("Cores dos LEDs","Não foi possível confirmar a aplicação. Abra o controle para verificar.",QSystemTrayIcon::Warning); }
        else { current=running; settings.setValue("color",current.name()); settings.setValue("brightness",runningBrightness); settings.sync(); tray.setIcon(swatch(QColor(current.red()*runningBrightness/100,current.green()*runningBrightness/100,current.blue()*runningBrightness/100))); setStatus(QString("%1 dispositivos sincronizados").arg(names.size())); }
        if(queued) QTimer::singleShot(0,launch);
    });
    auto choose=[&](QColor color){ if(!color.isValid()) return; pending=color; updatePreview(); launch(); };
    const QList<QPair<QString,QString>> colors={{"Azul","#0000ff"},{"Ciano","#00c8ff"},{"Verde","#00ff00"},{"Amarelo","#ffcc00"},{"Vermelho","#ff0000"},{"Roxo","#8000ff"},{"Branco","#ffffff"},{"Apagar","#000000"}};
    int index=0;
    for(auto preset:colors) {
        QColor color(preset.second);
        auto action=menu.addAction(swatch(color),preset.first); QObject::connect(action,&QAction::triggered,[&,color]{choose(color);});
        auto button=new QPushButton(swatch(color),QString()); button->setIconSize(QSize(26,26)); button->setToolTip(preset.first); button->setAccessibleName(preset.first); button->setMinimumHeight(44); presets->addWidget(button,index/4,index%4); ++index;
        QObject::connect(button,&QPushButton::clicked,[&,color]{choose(color);});
    }
    auto selectColor=[&]{ QColor color=QColorDialog::getColor(pending,nullptr,"Escolher cor dos LEDs"); if(color.isValid()) choose(color); };
    QObject::connect(custom,&QPushButton::clicked,selectColor); QObject::connect(preview,&QPushButton::clicked,selectColor);
    QObject::connect(brightness,&QSlider::valueChanged,[&](int value){pendingBrightness=value; brightnessLabel->setText(QString("Brilho · %1%").arg(value)); updatePreview();});
    QObject::connect(brightness,&QSlider::sliderReleased,launch);
    QTimer debounce; debounce.setSingleShot(true); debounce.setInterval(500);
    QObject::connect(brightness,&QSlider::valueChanged,[&]{debounce.start();}); QObject::connect(&debounce,&QTimer::timeout,launch);
    QObject::connect(retry,&QPushButton::clicked,launch);
    menu.addSeparator();
    auto pick=menu.addAction("Escolher cor…"); QObject::connect(pick,&QAction::triggered,selectColor);
    auto open=menu.addAction("Abrir controle…"); auto show=[&]{
        if(window.isVisible()) { window.hide(); return; }
        QPoint anchor=QCursor::pos();
        QRect icon=tray.geometry();
        if(icon.isValid()) anchor=QPoint(icon.center().x(),icon.bottom());
        // Use the actual Plasma tray bounds, also when activation comes from D-Bus.
        QProcess panelBounds;
        panelBounds.start("/usr/bin/qdbus", {"org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript",
            "var p=panels().filter(p=>p.location==='top')[0]; if(p){var t=p.widgets().filter(w=>w.type==='org.kde.plasma.systemtray')[0]; if(t) print(JSON.stringify(t.geometry));}"});
        if(panelBounds.waitForFinished(1000)) {
            auto rect=QJsonDocument::fromJson(panelBounds.readAllStandardOutput()).object();
            if(rect.contains("x")) {
                QRect trayBounds(rect["x"].toInt(),rect["y"].toInt(),rect["width"].toInt(),rect["height"].toInt());
                int anchorX=trayBounds.contains(anchor)?anchor.x():trayBounds.left()+16;
                anchor=QPoint(anchorX,trayBounds.bottom());
            }
        }
        auto screen=QGuiApplication::screenAt(anchor); if(!screen) screen=QGuiApplication::primaryScreen();
        QRect available=screen->availableGeometry();
        window.adjustSize();
        int x=qBound(available.left()+8,anchor.x()-window.width()/2,available.right()-window.width()-8);
        int y=qMax(available.top()+8,anchor.y()+10);
        y=qMin(y,available.bottom()-window.height()-8);
        window.move(x,y); window.show(); window.raise(); window.activateWindow();
    }; QObject::connect(open,&QAction::triggered,show);
    auto diagnostic=menu.addAction("Ver diagnóstico"); QObject::connect(diagnostic,&QAction::triggered,[&]{ QDesktopServices::openUrl(QUrl::fromLocalFile(base+"/last-run.log")); });
    menu.addSeparator(); auto quit=menu.addAction("Sair do controle"); QObject::connect(quit,&QAction::triggered,&app,&QApplication::quit);
    tray.setContextMenu(&menu); tray.show();
    QObject::connect(&tray,&QSystemTrayIcon::activated,[&](QSystemTrayIcon::ActivationReason reason){if(reason==QSystemTrayIcon::Trigger) show();});
    QObject::connect(&server,&QLocalServer::newConnection,[&]{auto socket=server.nextPendingConnection(); if(socket){socket->deleteLater();show();}});
    updatePreview(); QTimer::singleShot(1500,launch);
    if(app.arguments().contains("--show")) show();
    QObject::connect(&app,&QApplication::aboutToQuit,[&]{if(process.state()!=QProcess::NotRunning){process.terminate();if(!process.waitForFinished(2000)){process.kill();process.waitForFinished(1000);}}});
    return app.exec();
}
