document.addEventListener("ProcessStarted", (e) => {
  swalSuccess.fire({
    title: e.detail.title,
    didOpen: () => {
      htmx.trigger(document.body, "ForceUpdateProcessBtn");
    }
  })
})

document.addEventListener("ProcessPaused", (e) => {
  swalSuccess.fire({
    title: e.detail.title,
    didOpen: () => {
      htmx.trigger(document.body, "ForceUpdateProcessBtn");
    }
  })
})

document.addEventListener("ProcessContinued", (e) => {
  swalSuccess.fire({
    title: e.detail.title,
    didOpen: () => {
      htmx.trigger(document.body, "ForceUpdateProcessBtn");
    }
  })
})

document.addEventListener("ProcessRestarted", (e) => {
  swalSuccess.fire({
    title: e.detail.title,
    didOpen: () => {
      htmx.trigger(document.body, "ForceUpdateProcessBtn");
    }
  })
})

document.addEventListener("ProcessStartedFail", (e) => {
  swalError.fire({
    title: e.detail.title
  })
})

document.addEventListener("ProcessPausedFail", (e) => {
  swalError.fire({
    title: e.detail.title
  })
})

document.addEventListener("ProcessContinuedFail", (e) => {
  swalError.fire({
    title: e.detail.title
  })
})

document.addEventListener("ProcessRestartedFail", (e) => {
  swalError.fire({
    title: e.detail.title
  })
})

let processCheckboxButtons = null;
let audioSegmentEditButtons = null;

htmx.on("htmx:afterSettle", (e) => {
  processCheckboxButtons = document.querySelectorAll('input[name="selected_process"]');
  if (processCheckboxButtons) {
    processCheckboxButtons.forEach(checkbox => {
      checkbox.addEventListener('click', function () {
        if (this.checked) {
          processCheckboxButtons.forEach(otherCheckbox => {
            if (otherCheckbox !== this) {
              otherCheckbox.disabled = true;
            }
          });
        } else {
          processCheckboxButtons.forEach(otherCheckbox => {
            otherCheckbox.disabled = false;
          });
        }
      });
    });
  }
  audioSegmentEditButtons = document.querySelectorAll('.audiosegment-edit-btn');
  if (audioSegmentEditButtons) {
    audioSegmentEditButtons.forEach(btn => {
      btn.addEventListener('click', function () {
        audioSegmentEditButtons.forEach(otherBtn => {
          if (otherBtn !== this) {
            otherBtn.disabled = true;
          }
        })
      })
    })
  }
})

document.addEventListener("shown.bs.modal", () => {
  const audioPlayer = document.getElementById("audio-player-modal");
  if (audioPlayer) {
    document.addEventListener("hidden.bs.modal", () => {
      audioPlayer.pause();
      audioPlayer.currentTime = 0;
    })
  }
})

htmx.on("htmx:afterSwap", (e) => {
  if (e.detail.target.id === "modal-secondary-dialog") {
    loadToolTip();
    const secondaryModal = new bootstrap.Modal(document.getElementById("modal-secondary"));
    secondaryModal.show();
  }
  const audioSegmentCancelarBtn = document.querySelectorAll(".audiosegment-cancelar-btn");
  if (audioSegmentCancelarBtn) {
    audioSegmentCancelarBtn.forEach(btn => {
      btn.addEventListener('click', function () {
        audioSegmentEditButtons.forEach(otherBtn => {
          otherBtn.disabled = false;
        })
      })
    })
  }
})

document.addEventListener("ObjectEditedRelatedIntra", (e) => {
  const reloadBtn = document.getElementById("audiosegment-cancelar-" + e.detail.object_pk);
  htmx.trigger(reloadBtn, "click");
  audioSegmentEditButtons = document.querySelectorAll('.audiosegment-edit-btn');
  audioSegmentEditButtons.forEach(btn => {
    btn.disabled = false;
  })
  loadToolTip();
  swalSuccess.fire({
    title: e.detail.title
  })
})
