/* ************************************************************************

   qxapp - the simcore frontend

   https://osparc.io

   Copyright:
     2018 IT'IS Foundation, https://itis.swiss

   License:
     MIT: https://opensource.org/licenses/MIT

   Authors:
     * Odei Maiz (odeimaiz)

************************************************************************ */

/* eslint no-warning-comments: "off" */

qx.Class.define("qxapp.component.widget.NodeDataManager", {
  extend: qx.ui.core.Widget,

  construct: function(node) {
    this.base(arguments);

    this.set({
      node: node
    });

    let fileManagerLayout = new qx.ui.layout.VBox(10);
    this._setLayout(fileManagerLayout);

    let treesLayout = new qx.ui.container.Composite(new qx.ui.layout.HBox(10));
    this._add(treesLayout, {
      flex: 1
    });

    let nodeTree = this.__nodeTree = this._createChildControlImpl("nodeTree");
    nodeTree.setDragMechnism(true);
    nodeTree.addListener("selectionChanged", () => {
      this.__selectionChanged("node");
    }, this);
    treesLayout.add(nodeTree, {
      flex: 1
    });

    let userTree = this.__userTree = this._createChildControlImpl("userTree");
    userTree.setDropMechnism(true);
    userTree.addListener("selectionChanged", () => {
      this.__selectionChanged("user");
    }, this);
    userTree.addListener("fileCopied", e => {
      this.__reloadUserTree();
    }, this);
    treesLayout.add(userTree, {
      flex: 1
    });

    let selectedFileLayout = this.__selectedFileLayout = this._createChildControlImpl("selectedFileLayout");
    selectedFileLayout.addListener("fileDeleted", () => {
      this.__reloadNodeTree();
      this.__reloadUserTree();
    }, this);

    this.__reloadNodeTree();
    this.__reloadUserTree();
  },

  properties: {
    node: {
      check: "qxapp.data.model.Node"
    }
  },

  members: {
    __nodeTree: null,
    __userTree: null,
    __selectedFileLayout: null,

    _createChildControlImpl: function(id) {
      let control;
      switch (id) {
        case "nodeTree":
        case "userTree":
          control = new qxapp.component.widget.FilesTree();
          break;
        case "selectedFileLayout":
          control = new qxapp.component.widget.FileLabelWithActions().set({
            alignY: "middle"
          });
          this._add(control);
          break;
      }

      return control || this.base(arguments, id);
    },

    __reloadNodeTree: function() {
      this.__nodeTree.populateTree(this.getNode().getNodeId());
    },

    __reloadUserTree: function() {
      this.__userTree.populateTree();
    },

    __selectionChanged: function(selectedTree) {
      let selectionData = null;
      if (selectedTree === "user") {
        this.__nodeTree.resetSelection();
        selectionData = this.__userTree.getSelectedFile();
      } else {
        this.__userTree.resetSelection();
        selectionData = this.__nodeTree.getSelectedFile();
      }
      if (selectionData) {
        this.__selectedFileLayout.itemSelected(selectionData["selectedItem"], selectionData["isFile"]);
      }
    }
  }
});
