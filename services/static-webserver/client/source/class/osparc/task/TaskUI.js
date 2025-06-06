/* ************************************************************************

   osparc - the simcore frontend

   https://osparc.io

   Copyright:
     2021 IT'IS Foundation, https://itis.swiss

   License:
     MIT: https://opensource.org/licenses/MIT

   Authors:
     * Odei Maiz (odeimaiz)

************************************************************************ */

qx.Class.define("osparc.task.TaskUI", {
  extend: qx.ui.core.Widget,

  construct: function() {
    this.base(arguments);

    const grid = new qx.ui.layout.Grid(5, 5);
    grid.setColumnFlex(1, 1);
    this._setLayout(grid);

    this.set({
      padding: 5,
      maxWidth: this.self().MAX_WIDTH,
      backgroundColor: "background-main-3"
    });

    this._buildLayout();
  },

  properties: {
    task: {
      check: "osparc.data.PollTask",
      init: null,
      nullable: false,
      apply: "__applyTask"
    },

    title: {
      check: "String",
      init: "",
      nullable: true,
      event: "changeTitle"
    },

    subtitle: {
      check: "String",
      init: "",
      nullable: true,
      event: "changeSubtitle"
    }
  },

  statics: {
    MAX_WIDTH: 300
  },

  members: {
    _createChildControlImpl: function(id) {
      let control;
      switch (id) {
        case "icon":
          control = new qx.ui.basic.Image("@FontAwesome5Solid/circle-notch/14").set({
            width: 25,
            alignY: "middle"
          });
          control.getContentElement().addClass("rotate");
          this._add(control, {
            column: 0,
            row: 0,
            rowSpan: 2
          });
          break;
        case "title":
          control = new qx.ui.basic.Label();
          this.bind("title", control, "value");
          this._add(control, {
            column: 1,
            row: 0
          });
          break;
        case "subtitle":
          control = new qx.ui.basic.Label();
          this.bind("subtitle", control, "value");
          this._add(control, {
            column: 1,
            row: 1
          });
          break;
        case "progress":
          control = new qx.ui.basic.Label("").set({
            alignY: "middle",
          });
          this._add(control, {
            column: 2,
            row: 0,
            rowSpan: 2
          });
          break;
        case "stop":
          control = new qx.ui.basic.Image("@MaterialIcons/close/16").set({
            width: 25,
            cursor: "pointer",
            visibility: "excluded",
            alignY: "middle"
          });
          this._add(control, {
            column: 3,
            row: 0,
            rowSpan: 2
          });
          break;
      }
      return control || this.base(arguments, id);
    },

    __applyTask: function(task) {
      task.addListener("updateReceived", e => this._updateHandler(e.getData()), this);

      const stopButton = this.getChildControl("stop");
      task.bind("abortHref", stopButton, "visibility", {
        converter: abortHref => abortHref ? "visible" : "excluded"
      });
      stopButton.addListener("tap", () => this._abortHandler(), this);
    },

    _updateHandler: function(data) {
      if (data["task_progress"]) {
        if ("message" in data["task_progress"] && !this.getChildControl("subtitle").getValue()) {
          this.getChildControl("subtitle").setValue(data["task_progress"]["message"]);
        }
        this.getChildControl("progress").setValue((osparc.data.PollTask.extractProgress(data) * 100) + "%");
      }
    },

    _abortHandler: function() {
      const msg = this.tr("Are you sure you want to cancel the task?");
      const win = new osparc.ui.window.Confirmation(msg).set({
        caption: this.tr("Cancel Task"),
        confirmText: this.tr("Cancel"),
        confirmAction: "delete"
      });
      win.getCancelButton().setLabel(this.tr("Ignore"));
      win.center();
      win.open();
      win.addListener("close", () => {
        if (win.getConfirmed()) {
          this.getTask().abortRequested();
        }
      }, this);
    },

    setIcon: function(source) {
      this.getChildControl("icon").getContentElement().removeClass("rotate");
      this.getChildControl("icon").setSource(source);
    },

    _buildLayout: function() {
      this.getChildControl("title");
      this.getChildControl("subtitle");
    }
  }
});
