"""Simple Qt GUI for setting a global assign across all patches of an ES-8 backup.

Run with:  python -m bulk_editor.gui
"""
from dataclasses import asdict
import json
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from . import mappings
from .data_models import PatchList


class PatchListWidget(QListWidget):
    """List with drag & drop reordering that we handle ourselves.

    Qt's built-in InternalMove removes and re-inserts items, which can lose
    entries; instead we work out the target row and let the window move the
    underlying patch data, then rebuild the list.
    """

    def __init__(self, on_move):
        super().__init__()
        self.on_move = on_move
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)

    def dragEnterEvent(self, event):
        if event.source() is self:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.source() is self:
            super().dragMoveEvent(event)  # draws the drop indicator line
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.source() is not self:
            event.ignore()
            return
        pos = event.position().toPoint()
        item = self.itemAt(pos)
        if item is None:
            dest = self.count()
        else:
            dest = self.row(item)
            if pos.y() > self.visualItemRect(item).center().y():
                dest += 1
        rows = [self.row(i) for i in self.selectedItems()]
        # Tell Qt nothing should be removed from the source.
        event.setDropAction(Qt.IgnoreAction)
        event.accept()
        self.on_move(rows, dest)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ES-8 Bulk Editor[*]")
        self.resize(720, 520)
        self.backup = None
        self.params = {}

        # File row
        self.file_label = QLabel("No backup loaded")
        open_btn = QPushButton("Open backup (.bel)…")
        open_btn.clicked.connect(self.open_backup)
        file_row = QHBoxLayout()
        file_row.addWidget(open_btn)
        file_row.addWidget(self.file_label, 1)

        # Patch list: Ctrl/Cmd-click two patches and press "Swap", or drag to reorder
        self.patch_list = PatchListWidget(self.move_rows)
        self.patch_list.itemSelectionChanged.connect(self.update_buttons)

        self.swap_btn = QPushButton("Swap selected (2)")
        self.swap_btn.setEnabled(False)
        self.swap_btn.clicked.connect(self.swap_selected)
        self.save_btn = QPushButton("Save backup as…")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_backup)
        self.up_btn = QPushButton("▲ Up")
        self.up_btn.setToolTip("Move selection up (Alt+Up)")
        self.up_btn.clicked.connect(lambda: self.shift_selected(-1))
        self.down_btn = QPushButton("▼ Down")
        self.down_btn.setToolTip("Move selection down (Alt+Down)")
        self.down_btn.clicked.connect(lambda: self.shift_selected(1))
        QShortcut(QKeySequence("Alt+Up"), self, lambda: self.shift_selected(-1))
        QShortcut(QKeySequence("Alt+Down"), self, lambda: self.shift_selected(1))
        list_buttons = QHBoxLayout()
        list_buttons.addWidget(self.up_btn)
        list_buttons.addWidget(self.down_btn)
        list_buttons.addWidget(self.swap_btn)
        list_buttons.addWidget(self.save_btn)
        left = QVBoxLayout()
        left.addWidget(self.patch_list, 1)
        left.addLayout(list_buttons)

        # Assign form
        self.assign_num = QSpinBox()
        self.assign_num.setRange(1, 12)
        self.source = QComboBox()
        self.source.addItems(mappings.PATCH_ASSIGN_SOURCE_ORDER)
        self.mode = QComboBox()
        self.mode.addItems(mappings.PATCH_ASSIGN_MODE_ORDER)
        self.mode.setCurrentText("TGL")
        self.target = QComboBox()
        self.target.addItems(mappings.PATCH_ASSIGN_TARGET_ORDER)
        self.params_label = QLabel("(none)")
        params_btn = QPushButton("Load params JSON…")
        params_btn.clicked.connect(self.load_params)
        params_row = QHBoxLayout()
        params_row.addWidget(params_btn)
        params_row.addWidget(self.params_label, 1)

        form = QFormLayout()
        form.addRow("Assign #", self.assign_num)
        form.addRow("Source", self.source)
        form.addRow("Mode", self.mode)
        form.addRow("Target", self.target)
        form.addRow("Params", params_row)

        self.apply_btn = QPushButton("Apply to all patches")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self.apply)

        right = QVBoxLayout()
        right.addLayout(form)
        right.addWidget(self.apply_btn)
        right.addStretch()

        body = QHBoxLayout()
        body.addLayout(left, 1)
        body.addLayout(right, 1)

        root = QVBoxLayout()
        root.addLayout(file_row)
        root.addLayout(body)
        w = QWidget()
        w.setLayout(root)
        self.setCentralWidget(w)

    def open_backup(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open ES-8 backup", "", "ES-8 backup (*.bel);;All files (*)"
        )
        if not path:
            return
        try:
            with open(path) as f:
                self.backup = json.load(f)
            patches = PatchList(self.backup["patch"]).patches
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load backup:\n{e}")
            return
        self.names = [p.patch_name for p in patches]
        self.refresh_list()
        self.file_label.setText(path)
        self.apply_btn.setEnabled(True)
        self.save_btn.setEnabled(True)

    def refresh_list(self, select=()):
        lst = self.patch_list
        lst.blockSignals(True)
        lst.clear()
        for i, name in enumerate(self.names):
            bank, num = mappings.index_to_patch(i)
            lst.addItem(f"{bank}:{num}  {name}")
        lst.blockSignals(False)
        for row in select:
            lst.item(row).setSelected(True)
        if select:
            lst.scrollToItem(lst.item(select[0]))
        self.update_buttons()

    def update_buttons(self):
        n = len(self.patch_list.selectedItems())
        self.swap_btn.setEnabled(n == 2)
        self.up_btn.setEnabled(n > 0)
        self.down_btn.setEnabled(n > 0)

    def swap_selected(self):
        a, b = self.selected_rows()
        p = self.backup["patch"]
        p[a], p[b] = p[b], p[a]
        self.names[a], self.names[b] = self.names[b], self.names[a]
        self.refresh_list(select=(a, b))
        self.setWindowModified(True)

    def selected_rows(self):
        return sorted(self.patch_list.row(i) for i in self.patch_list.selectedItems())

    def move_rows(self, rows, dest):
        """Move the given rows so they sit before `dest` (an index in the
        current list); everything in between shifts up or down. Nothing is
        ever dropped: the data is re-ordered, never removed."""
        if not rows or self.backup is None:
            return
        rows = sorted(set(rows))
        n_before = sum(1 for r in rows if r < dest)
        insert_at = dest - n_before
        for lst in (self.backup["patch"], self.names):
            moved = [lst[r] for r in rows]
            for r in reversed(rows):
                del lst[r]
            lst[insert_at:insert_at] = moved
        assert len(self.backup["patch"]) == len(self.names)
        self.refresh_list(select=tuple(range(insert_at, insert_at + len(rows))))
        self.setWindowModified(True)

    def shift_selected(self, step):
        rows = self.selected_rows()
        if not rows:
            return
        if step < 0 and rows[0] > 0:
            self.move_rows(rows, rows[0] - 1)
        elif step > 0 and rows[-1] < len(self.names) - 1:
            self.move_rows(rows, rows[-1] + 2)

    def save_backup(self):
        out, _ = QFileDialog.getSaveFileName(
            self, "Save backup", "output.bel", "ES-8 backup (*.bel)"
        )
        if not out:
            return
        with open(out, "w") as f:
            json.dump(self.backup, f)
        self.setWindowModified(False)
        self.statusBar().showMessage(f"Saved to {out}")
        QMessageBox.information(self, "Done", f"Saved to {out}")

    def load_params(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open params JSON", "", "JSON (*.json);;All files (*)"
        )
        if not path:
            return
        try:
            with open(path) as f:
                self.params = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load params:\n{e}")
            return
        self.params_label.setText(path)

    def apply(self):
        """Apply the assign to all patches in memory. Use "Save backup as…"
        to write the result; further bulk edits can be stacked first."""
        try:
            patch_list = PatchList(self.backup["patch"])
            patches, _ = patch_list.update_assign(
                assign_number=self.assign_num.value(),
                source=self.source.currentText(),
                mode=self.mode.currentText(),
                target=self.target.currentText(),
                params=self.params,
            )
            new_patches = [asdict(p) for p in patches]
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply assign:\n{e}")
            return
        self.backup["patch"] = new_patches
        self.names = [p.patch_name for p in PatchList(new_patches).patches]
        self.refresh_list(select=tuple(self.selected_rows()))
        self.setWindowModified(True)
        self.statusBar().showMessage(
            f"Applied assign {self.assign_num.value()}: {self.source.currentText()} "
            f"→ {self.target.currentText()} ({self.mode.currentText()}). Not saved yet."
        )


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
