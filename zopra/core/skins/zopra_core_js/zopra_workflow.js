$(document).ready(function () {
    //workflow buttons get disabled on form field change
    $(".field input, .field select, .field textarea").change(function () {
        $("input[name='form.button.ChangeWorkflowState1'], input[name='form.button.ChangeWorkflowState2'], input[name='form.button.ChangeWorkflowState3']")
            .attr("disabled", "disabled");
    });
});