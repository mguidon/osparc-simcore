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


qx.Class.define("osparc.info.StudyUtils", {
  type: "static",

  statics: {
    /**
      * @param study {osparc.data.model.Study} Study Model
      */
    createTitle: function(study) {
      const title = osparc.info.Utils.createTitle();
      study.bind("name", title, "value");
      return title;
    },

    /**
      * @param study {osparc.data.model.Study} Study Model
      */
    createUuid: function(study) {
      const uuid = osparc.info.Utils.createLabel();
      study.bind("uuid", uuid, "value");
      study.bind("uuid", uuid, "toolTipText");
      return uuid;
    },

    /**
      * @param study {osparc.data.model.Study} Study Model
      */
    createOwner: function(study) {
      const owner = new qx.ui.basic.Label();
      study.bind("prjOwner", owner, "value", {
        converter: email => {
          if (email === osparc.auth.Data.getInstance().getEmail()) {
            return qx.locale.Manager.tr("me");
          }
          return osparc.utils.Utils.getNameFromEmail(email);
        },
        onUpdate: (source, target) => {
          target.setToolTipText(source.getPrjOwner());
        }
      });
      return owner;
    },

    /**
      * @param study {osparc.data.model.Study} Study Model
      */
    createCreationDate: function(study) {
      const creationDate = new qx.ui.basic.Label();
      study.bind("creationDate", creationDate, "value", {
        converter: date => osparc.utils.Utils.formatDateAndTime(date)
      });
      return creationDate;
    },

    /**
      * @param study {osparc.data.model.Study} Study Model
      */
    createLastChangeDate: function(study) {
      const lastChangeDate = new qx.ui.basic.Label();
      study.bind("lastChangeDate", lastChangeDate, "value", {
        converter: date => osparc.utils.Utils.formatDateAndTime(date)
      });
      return lastChangeDate;
    },

    /**
      * @param study {osparc.data.model.Study} Study Model
      */
    createAccessRights: function(study) {
      const accessRights = new qx.ui.basic.Label();
      let permissions = "";
      const myGID = osparc.auth.Data.getInstance().getGroupId();
      const ar = study.getAccessRights();
      if (myGID in ar) {
        if (ar[myGID]["delete"]) {
          permissions = qx.locale.Manager.tr("Owner");
        } else if (ar[myGID]["write"]) {
          permissions = qx.locale.Manager.tr("Editor");
        } else if (ar[myGID]["read"]) {
          permissions = qx.locale.Manager.tr("User");
        }
      }
      accessRights.setValue(permissions);
      return accessRights;
    },

    /**
      * @param study {osparc.data.model.Study} Study Model
      */
    createShared: function(study) {
      const isShared = new qx.ui.basic.Label();
      const populateLabel = () => {
        const nCollabs = Object.keys(study.getAccessRights()).length;
        isShared.setValue(nCollabs === 1 ? qx.locale.Manager.tr("Not Shared") : "+" + String(nCollabs-1));
      }
      study.addListener("changeAccessRights", () => populateLabel());
      populateLabel();
      return isShared;
    },

    /**
      * @param study {osparc.data.model.Study} Study Model
      */
    createClassifiers: function(study) {
      const nClassifiers = new qx.ui.basic.Label();
      study.bind("classifiers", nClassifiers, "value", {
        converter: classifiers => `(${classifiers.length})`
      });
      return nClassifiers;
    },

    /**
      * @param study {osparc.data.model.Study} Study Model
      */
    createQuality: function(study) {
      const tsrLayout = new qx.ui.container.Composite(new qx.ui.layout.HBox(2)).set({
        toolTipText: qx.locale.Manager.tr("Ten Simple Rules score")
      });
      const addStars = model => {
        tsrLayout.removeAll();
        const quality = model.getQuality();
        if (osparc.metadata.Quality.isEnabled(quality)) {
          const tsrRating = new osparc.ui.basic.StarsRating();
          tsrRating.set({
            nStars: 4,
            showScore: true
          });
          osparc.ui.basic.StarsRating.scoreToStarsRating(quality["tsr_current"], quality["tsr_target"], tsrRating);
          tsrLayout.add(tsrRating);
        } else {
          tsrLayout.exclude();
        }
      };
      study.addListener("changeQuality", () => addStars(study), this);
      addStars(study);
      return tsrLayout;
    },

    /**
      * @param study {osparc.data.model.Study} Study Model
      * @param maxWidth {Number} thumbnail's maxWidth
      * @param maxHeight {Number} thumbnail's maxHeight
      */
    createThumbnail: function(study, maxWidth, maxHeight) {
      const thumbnail = osparc.info.Utils.createThumbnail(maxWidth, maxHeight);
      const noThumbnail = "osparc/no_photography_black_24dp.svg";
      study.bind("thumbnail", thumbnail, "source", {
        converter: thumb => thumb ? thumb : noThumbnail,
        onUpdate: (source, target) => {
          if (source.getThumbnail() === "") {
            target.getChildControl("image").set({
              minWidth: 120,
              minHeight: 139
            });
          }
        }
      });
      return thumbnail;
    },

    /**
      * @param study {osparc.data.model.Study} Study Model
      * @param maxHeight {Number} description's maxHeight
      */
    createDescriptionMD: function(study, maxHeight) {
      const description = new osparc.ui.markdown.Markdown();
      study.bind("description", description, "value", {
        converter: desc => desc ? desc : "Add description"
      });
      const scrollContainer = new qx.ui.container.Scroll();
      if (maxHeight) {
        scrollContainer.setMaxHeight(maxHeight);
      }
      scrollContainer.add(description);
      return scrollContainer;
    },

    /**
      * @param study {osparc.data.model.Study} Study Model
      */
    createDisableServiceAutoStart: function(study) {
      // the wording is now opposite to the value of the property
      // Autostart services to true by default
      const devObj = study.getDev();
      const cb = new qx.ui.form.CheckBox().set({
        value: "disableServiceAutoStart" in devObj ? !devObj["disableServiceAutoStart"] : true,
        label: qx.locale.Manager.tr("Autostart services"),
        font: "text-14",
        toolTipText: qx.locale.Manager.tr("Disabling this will help opening and closing studies/projects faster"),
        iconPosition: "right"
      });
      cb.addListener("changeValue", e => {
        const newVal = e.getData();
        const devObjCopy = osparc.utils.Utils.deepCloneObject(devObj);
        devObjCopy["disableServiceAutoStart"] = !newVal;
        study.patchStudy({"dev": devObjCopy});
      });
      return cb;
    },

    /**
      * @param study {osparc.data.model.Study} Study Model
      */
    createTags: function(study) {
      const tagsContainer = new qx.ui.container.Composite(new qx.ui.layout.Flow(5, 5)).set({
        maxWidth: 420
      });

      const addTags = model => {
        tagsContainer.removeAll();
        const noTagsLabel = new qx.ui.basic.Label(qx.locale.Manager.tr("Add tags"));
        tagsContainer.add(noTagsLabel);
        osparc.store.Tags.getInstance().getTags().filter(tag => model.getTags().includes(tag.getTagId()))
          .forEach(selectedTag => {
            if (tagsContainer.indexOf(noTagsLabel) > -1) {
              tagsContainer.remove(noTagsLabel);
            }
            tagsContainer.add(new osparc.ui.basic.Tag(selectedTag));
          });
      };
      study.addListener("changeTags", () => addTags(study), this);
      osparc.store.Tags.getInstance().addListener("tagsChanged", () => addTags(study), this);
      addTags(study);

      return tagsContainer;
    },

    __titleWithEditLayout: function(data, titleWidth = 75) {
      const titleLayout = new qx.ui.container.Composite(new qx.ui.layout.HBox(5));
      const hasButton = Boolean(data.action && data.action.button);
      // use the width for aligning the buttons
      const title = new qx.ui.basic.Label(data.label).set({
        allowGrowX: true,
        maxWidth: hasButton ? titleWidth : titleWidth + 35 // spacer for the button
      });
      titleLayout.add(title, {
        flex: 1
      });
      if (hasButton) {
        const button = data.action.button;
        titleLayout.add(button);
        button.addListener("execute", () => {
          const cb = data.action.callback;
          if (typeof cb === "string") {
            data.action.ctx.fireEvent(cb);
          } else {
            cb.call(data.action.ctx);
          }
        }, this);
      }
      return titleLayout;
    },

    infoElementsToLayout: function(extraInfos) {
      const positions = {
        TITLE: {
          column: 0,
          row: 0,
        },
        THUMBNAIL: {
          column: 0,
          row: 1,
        },
        DESCRIPTION: {
          column: 0,
          row: 2,
        },
        AUTHOR: {
          inline: true,
          column: 0,
          row: 0,
        },
        CREATED: {
          inline: true,
          column: 0,
          row: 1,
        },
        MODIFIED: {
          inline: true,
          column: 0,
          row: 2,
        },
        ACCESS_RIGHTS: {
          inline: true,
          column: 0,
          row: 3,
        },
        TAGS: {
          inline: true,
          column: 0,
          row: 4,
        },
        QUALITY: {
          inline: true,
          column: 0,
          row: 5,
        },
        CLASSIFIERS: {
          inline: true,
          column: 0,
          row: 6,
        },
        LOCATION: {
          inline: true,
          column: 0,
          row: 7,
        },
      };

      const mainInfoGrid = new qx.ui.layout.Grid(15, 5);
      mainInfoGrid.setColumnAlign(0, "left", "top");
      mainInfoGrid.setColumnFlex(0, 1);
      const mainInfoLayout = new qx.ui.container.Composite(mainInfoGrid);

      const extraInfoGrid = new qx.ui.layout.Grid(15, 5);
      const extraInfoLayout = new qx.ui.container.Composite(extraInfoGrid);
      extraInfoGrid.setColumnFlex(0, 1);

      let row = 0;
      let row2 = 0;
      Object.keys(positions).forEach(key => {
        if (key in extraInfos) {
          const extraInfo = extraInfos[key];
          const gridInfo = positions[key];

          if (gridInfo.inline) {
            const titleLayout = this.__titleWithEditLayout(extraInfo);
            if (extraInfo.action && extraInfo.action.button) {
              extraInfo.action.button.set({
                marginRight: 15
              });
            }
            titleLayout.add(extraInfo.view, {
              flex: 1
            });
            extraInfoLayout.add(titleLayout, {
              row: row2,
              column: gridInfo.column
            });
            row2++;
            extraInfoGrid.setRowHeight(row2, 5); // spacer
            row2++;
          } else {
            const titleLayout = this.__titleWithEditLayout(extraInfo);
            mainInfoLayout.add(titleLayout, {
              row,
              column: gridInfo.column
            });
            row++;
            mainInfoLayout.add(extraInfo.view, {
              row,
              column: gridInfo.column
            });
            row++;
            mainInfoGrid.setRowHeight(row, 5); // spacer
            row++;
          }
        }
      });


      const container = new qx.ui.container.Composite(new qx.ui.layout.VBox());
      const box1 = this.__createSectionBox(qx.locale.Manager.tr("Details"));
      box1.add(mainInfoLayout);
      container.addAt(box1, 0);

      const box2 = this.__createSectionBox(qx.locale.Manager.tr("Meta details"));
      box2.add(extraInfoLayout);
      container.addAt(box2, 1);

      return container;
    },

    /**
      * @param studyData {Object} Serialized Study Object
      */
    openAccessRights: function(studyData) {
      const permissionsView = new osparc.share.CollaboratorsStudy(studyData);
      const title = qx.locale.Manager.tr("Share with Editors and Organizations");
      osparc.ui.window.Window.popUpInWindow(permissionsView, title, 500, 500);
      return permissionsView;
    },

    /**
      * @param resourceData {Object} Serialized Resource Object
      */
    openQuality: function(resourceData) {
      const qualityEditor = new osparc.metadata.QualityEditor(resourceData);
      const title = resourceData["name"] + " - " + qx.locale.Manager.tr("Quality Assessment");
      osparc.ui.window.Window.popUpInWindow(qualityEditor, title, 650, 700);
      return qualityEditor;
    },

    /**
     * Common layout of section's box
     * @param {page section's name} sectionName
     */
    __createSectionBox: function(sectionName) {
      const box = new qx.ui.groupbox.GroupBox(sectionName);
      box.getChildControl("legend").set({
        font: "text-14"
      });
      box.getChildControl("frame").set({
        backgroundColor: "transparent"
      });
      box.setLayout(new qx.ui.layout.VBox(10));
      return box;
    },
  }
});
