from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu, QMessageBox
from qgis.core import QgsApplication

import processing
import unicodedata


class ImovelGeoFerramentas:
    """Barra de atalhos para ferramentas do QGIS e do LFTOOLs."""

    def __init__(self, iface):
        self.iface = iface
        self.menu = None
        self.actions = []

    def tr(self, text):
        return QCoreApplication.translate("ImovelGeoFerramentas", text)

    def initGui(self):
        self.menu = QMenu("ImovelGEO Ferramentas", self.iface.mainWindow())
        self._insert_menu_after_cggeo()

        qgis_menu = QMenu("QGIS", self.menu)
        lftools_menu = QMenu("LF Tools", self.menu)
        self.menu.addMenu(qgis_menu)
        self.menu.addMenu(lftools_menu)

        self._add_processing_action(
            "Poligonizar",
            "Cria polígonos a partir de regiões raster conectadas.",
            "native:polygonize",
            qgis_menu,
        )
        self._add_processing_action(
            "Recortar",
            "Recorta uma camada vetorial usando outra camada como máscara.",
            "native:clip",
            qgis_menu,
        )
        self._add_processing_action(
            "Corrigir geometria",
            "Corrige geometrias inválidas da camada vetorial.",
            "native:fixgeometries",
            qgis_menu,
        )
        self._add_georeferencer_action(qgis_menu)

        self._add_lftools_action(
            "Azimute e Distância",
            "Abre a ferramenta Azimute e Distância do LF Tools.",
            "Azimute e Distância",
            lftools_menu,
        )
        self._add_lftools_action(
            "Poligonal Fechada",
            "Abre a ferramenta Poligonal Fechada do LF Tools.",
            "Poligonal Fechada",
            lftools_menu,
        )

    def _insert_menu_after_cggeo(self):
        menu_bar = self.iface.mainWindow().menuBar()
        menu_action = self.menu.menuAction()
        menu_actions = menu_bar.actions()
        cgggeo_action = next(
            (
                action
                for action in menu_actions
                if action.text().replace("&", "").strip().lower()
                == "cgggeo tools 1.2"
            ),
            None,
        )

        if cgggeo_action is None:
            menu_bar.addAction(menu_action)
            return

        position = menu_actions.index(cgggeo_action)
        following_action = (
            menu_actions[position + 1]
            if position + 1 < len(menu_actions)
            else None
        )
        menu_bar.insertAction(following_action, menu_action)

    def _add_processing_action(self, label, tooltip, algorithm_id, menu):
        action = QAction(QIcon(), label, self.iface.mainWindow())
        action.setToolTip(tooltip)
        action.triggered.connect(
            lambda checked=False, algorithm_id=algorithm_id: processing.execAlgorithmDialog(
                algorithm_id, {}
            )
        )
        menu.addAction(action)
        self.actions.append(action)

    def _add_georeferencer_action(self, menu):
        action = QAction(QIcon(), "Georreferenciamento", self.iface.mainWindow())
        action.setToolTip("Abre o Georreferenciador nativo do QGIS.")
        action.triggered.connect(self._open_georeferencer)
        menu.addAction(action)
        self.actions.append(action)

    def _open_georeferencer(self):
        action = self.iface.mainWindow().findChild(
            QAction, "mActionShowGeoreferencer"
        )
        if action is None:
            QMessageBox.warning(
                self.iface.mainWindow(),
                "ImovelGEO Ferramentas",
                "A ferramenta 'Georreferenciamento' não foi encontrada. "
                "Verifique se o complemento nativo Georreferenciador está "
                "habilitado no QGIS.",
            )
            return
        action.trigger()

    def _add_lftools_action(self, label, tooltip, expected_name, menu):
        action = QAction(QIcon(), label, self.iface.mainWindow())
        action.setToolTip(tooltip)
        action.triggered.connect(
            lambda checked=False, expected_name=expected_name: self._open_lftools_algorithm(
                expected_name
            )
        )
        menu.addAction(action)
        self.actions.append(action)

    def _open_lftools_algorithm(self, expected_name):
        algorithm = self._find_lftools_algorithm(expected_name)
        if algorithm is None:
            QMessageBox.warning(
                self.iface.mainWindow(),
                "ImovelGEO Ferramentas",
                f"A ferramenta '{expected_name}' não foi encontrada. "
                "Verifique se o complemento LF Tools está instalado e habilitado "
                "em Complementos > Gerenciar e Instalar Complementos.",
            )
            return
        processing.execAlgorithmDialog(algorithm.id(), {})

    def _find_lftools_algorithm(self, expected_name):
        """Localiza um algoritmo LF Tools pelo provedor e nome exibido."""
        expected = self._normalize(expected_name)
        registry = QgsApplication.processingRegistry()

        for algorithm in registry.algorithms():
            provider_id = algorithm.provider().id().lower()
            name = self._normalize(algorithm.displayName())
            if "lftools" in provider_id and expected in name:
                return algorithm
        return None

    @staticmethod
    def _normalize(text):
        normalized = unicodedata.normalize("NFKD", text)
        return "".join(
            character for character in normalized
            if not unicodedata.combining(character)
        ).lower().strip()

    def unload(self):
        for action in self.actions:
            action.deleteLater()
        self.actions.clear()

        if self.menu is not None:
            self.iface.mainWindow().menuBar().removeAction(self.menu.menuAction())
            self.menu.deleteLater()
            self.menu = None
