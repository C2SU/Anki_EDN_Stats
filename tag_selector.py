"""
Tag Selector Dialog - Extracted from BetterSearch addon
Original work Copyright (c): 2018 Rene Schallner
Modified work Copyright (c): 2019- ijgnd
License: GNU General Public License v3
"""
from aqt.qt import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QColor,
    QDialog,
    QEvent,
    QHBoxLayout,
    QKeySequence,
    QLabel,
    QLineEdit,
    QListWidget,
    QPen,
    QPushButton,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    Qt,
    QVBoxLayout,
    QWidget,
    pyqtSignal,
    pyqtSlot,
)
from aqt.utils import tooltip, restoreGeom, saveGeom
import aqt


class HighlightDelegate(QStyledItemDelegate):
    """Delegate pour surligner les termes de recherche dans les éléments de la liste."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filters = []
        self._highlightColor = QColor(Qt.GlobalColor.red)

    def paint(self, painter, option, index):
        painter.save()
        viewOption = QStyleOptionViewItem(option)
        self.initStyleOption(viewOption, index)
        text = viewOption.text
        viewOption.text = ""
        style = viewOption.widget.style() if viewOption.widget else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, viewOption, painter)
        textRect = style.subElementRect(QStyle.SubElement.SE_ItemViewItemText, viewOption)
        painter.setClipRect(textRect)
        painter.translate(textRect.topLeft())
        if option.state & QStyle.StateFlag.State_Selected:
            normalPen = QPen(viewOption.palette.highlightedText().color())
        else:
            normalPen = QPen(viewOption.palette.text().color())
        segments = self._segment_text(text, self.filters)
        fm = viewOption.fontMetrics
        x = 0
        baseline = fm.ascent()
        for segment, isHighlighted in segments:
            width = fm.horizontalAdvance(segment)
            if isHighlighted:
                painter.setPen(self._highlightColor)
            else:
                painter.setPen(normalPen)
            painter.drawText(x, baseline, segment)
            x += width
        painter.restore()

    def _segment_text(self, text, filters):
        """Découpe le texte en segments normaux et surlignés."""
        if not filters or not text:
            return [(text, False)]
        intervals = []
        lower_text = text.lower()
        for flt in filters:
            flt_lower = flt.lower()
            start = 0
            while True:
                idx = lower_text.find(flt_lower, start)
                if idx == -1:
                    break
                intervals.append((idx, idx + len(flt)))
                start = idx + len(flt)
        if not intervals:
            return [(text, False)]
        intervals.sort(key=lambda x: x[0])
        merged = []
        current_start, current_end = intervals[0]
        for i in range(1, len(intervals)):
            st, en = intervals[i]
            if st <= current_end:
                current_end = max(current_end, en)
            else:
                merged.append((current_start, current_end))
                current_start, current_end = st, en
        merged.append((current_start, current_end))
        segments = []
        last_end = 0
        for (start_i, end_i) in merged:
            if start_i > last_end:
                segments.append((text[last_end:start_i], False))
            segments.append((text[start_i:end_i], True))
            last_end = end_i
        if last_end < len(text):
            segments.append((text[last_end:], False))
        return segments

    @pyqtSlot(list)
    def setFilters(self, filters):
        if self.filters != filters:
            self.filters = filters


class PanelInputLine(QLineEdit):
    """Champ de saisie avec gestion des touches haut/bas pour naviguer dans la liste."""
    
    down_pressed = pyqtSignal()
    up_pressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        mod = aqt.mw.app.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier
        key = event.key()
        if key == Qt.Key.Key_Down:
            self.down_pressed.emit()
        elif key == Qt.Key.Key_Up:
            self.up_pressed.emit()
        elif mod and (key == Qt.Key.Key_N):
            self.down_pressed.emit()
        elif mod and (key == Qt.Key.Key_P):
            self.up_pressed.emit()


class TagSelectorDialog(QDialog):
    """
    Boîte de dialogue pour sélectionner des tags avec filtrage fuzzy.
    """
    
    silentlyClose = True

    def __init__(
        self,
        parent=None,
        tags=None,
        windowtitle="Sélectionner un tag",
        max_items=1500,
        multi_selection=False,
        sort_tags=True,
        show_negation_checkbox=False,
        highlight_matches=True,
        context="edn_tag_selector",
    ):
        super().__init__(parent)
        aqt.mw.garbage_collect_on_dialog_finish(self)
        
        self.parent = parent
        self.max_items = max_items
        self.multi_selection = multi_selection
        self.highlight_matches = highlight_matches
        self.show_negation_checkbox = show_negation_checkbox
        self.context = context
        
        self.endswith_sign = "$$"
        self.exclude_sign = "!"
        self.startswith_sign = "^"
        
        self.setObjectName("TagSelectorDialog")
        if windowtitle:
            self.setWindowTitle(windowtitle)
        
        if tags is None:
            tags = []
        self.keys = sorted(tags) if sort_tags else list(tags)
        self.matched_items = self.keys
        
        self.sel_keys_list = []
        self.neg = False
        
        self._initUI()

    def _initUI(self):
        """Initialise l'interface utilisateur."""
        vlay = QVBoxLayout()
        
        self.input_line = PanelInputLine()
        self.input_line.setPlaceholderText("Tapez pour rechercher (ex: cardio, 123, hyper...)")
        vlay.addWidget(self.input_line)
        
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        
        if self.multi_selection:
            self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        
        if self.highlight_matches:
            self.delegate = HighlightDelegate(self.list_widget)
            self.list_widget.setItemDelegate(self.delegate)
        
        for i in range(self.max_items):
            self.list_widget.insertItem(i, "")
        
        vlay.addWidget(self.list_widget)
        
        self.label_not_all_shown = QLabel()
        vlay.addWidget(self.label_not_all_shown)
        
        info_text = "<small><b>↑↓</b> naviguer | <b>Entrée</b> valider | Double-clic sélectionner</small>"
        info_label = QLabel(info_text)
        vlay.addWidget(info_label)
        
        button_box = QHBoxLayout()
        
        self.cb_neg = QCheckBox("Ajouter '-' (exclusion)")
        if self.show_negation_checkbox:
            button_box.addWidget(self.cb_neg)
        
        button_box.addStretch(1)
        
        self.button_ok = QPushButton("&OK", self)
        self.button_ok.clicked.connect(self.accept)
        button_box.addWidget(self.button_ok)
        
        self.button_cancel = QPushButton("&Annuler", self)
        self.button_cancel.clicked.connect(self.reject)
        button_box.addWidget(self.button_cancel)
        
        vlay.addLayout(button_box)
        
        self._update_listwidget()
        self.setLayout(vlay)
        self.resize(600, 400)
        restoreGeom(self, f"TagSelector-{self.context}")
        
        self.input_line.textChanged.connect(self._text_changed)
        self.input_line.returnPressed.connect(self.accept)
        self.input_line.down_pressed.connect(self._down_pressed)
        self.input_line.up_pressed.connect(self._up_pressed)
        self.list_widget.itemDoubleClicked.connect(self.accept)
        self.list_widget.installEventFilter(self)
        self.input_line.setFocus()

    def _update_listwidget(self):
        """Met à jour la liste affichée."""
        for i in range(self.max_items):
            item = self.list_widget.item(i)
            if i < len(self.matched_items):
                item.setHidden(False)
                item.setText(self.matched_items[i])
            else:
                item.setHidden(True)
        
        self.list_widget.setCurrentRow(0)
        
        if self.highlight_matches:
            term_tuples = self._split_search_terms(self.input_line.text())
            terms = [item[3] for item in term_tuples if item[0]]
            self.delegate.setFilters(terms)
            self.list_widget.viewport().update()
        
        if len(self.matched_items) > self.max_items:
            self.label_not_all_shown.setText(
                f"Affichage de {self.max_items} sur {len(self.matched_items)} résultats."
            )
            self.label_not_all_shown.setVisible(True)
        else:
            self.label_not_all_shown.setVisible(False)

    def _text_changed(self):
        """Appelé quand le texte de recherche change."""
        search_string = self.input_line.text()
        self.matched_items = self._process_search(search_string, self.keys)
        
        if search_string in self.matched_items:
            self.matched_items.insert(
                0, self.matched_items.pop(self.matched_items.index(search_string))
            )
        
        self._update_listwidget()

    def _process_search(self, search_terms, keys):
        """Filtre les tags selon les termes de recherche (simple contains)."""
        if not search_terms.strip():
            return keys
        
        # Simple contains-matching for each word
        terms = search_terms.lower().split()
        results = []
        for elem in keys:
            elem_lower = elem.lower()
            # All terms must be present in the tag
            if all(term in elem_lower for term in terms):
                results.append(elem)
        
        return results

    def _split_search_terms(self, search_string):
        """Découpe la chaîne de recherche en termes simples pour le highlighting."""
        if not search_string.strip():
            return []
        terms = search_string.lower().split()
        # Return tuples in format (presence=True, atstart=False, atend=False, term)
        return [(True, False, False, term) for term in terms]

    def _up_pressed(self):
        """Navigation vers le haut dans la liste."""
        row = self.list_widget.currentRow()
        if row == 0:
            self.list_widget.setCurrentRow(len(self.matched_items) - 1)
        else:
            self.list_widget.setCurrentRow(row - 1)

    def _down_pressed(self):
        """Navigation vers le bas dans la liste."""
        row = self.list_widget.currentRow()
        if row == len(self.matched_items) - 1:
            self.list_widget.setCurrentRow(0)
        else:
            self.list_widget.setCurrentRow(row + 1)

    def reject(self):
        """Ferme le dialogue sans sélection."""
        saveGeom(self, f"TagSelector-{self.context}")
        QDialog.reject(self)

    def accept(self):
        """Valide la sélection."""
        sel_rows = [item.row() for item in self.list_widget.selectedIndexes()]
        if not sel_rows or len(self.matched_items) == 0:
            tooltip("Aucune sélection. Annulation...")
            return
        
        saveGeom(self, f"TagSelector-{self.context}")
        self.sel_keys_list = [self.matched_items[row] for row in sel_rows]
        self.neg = self.cb_neg.isChecked()
        QDialog.accept(self)

    def eventFilter(self, watched, event):
        """Gère les événements clavier sur la liste."""
        if event.type() == QEvent.Type.KeyPress and event.matches(QKeySequence.StandardKey.InsertParagraphSeparator):
            self.accept()
            return True
        return QWidget.eventFilter(self, watched, event)
