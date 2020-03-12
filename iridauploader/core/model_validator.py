from cerberus import Validator

import iridauploader.model as model


def validate_sequencing_run(sequencing_run):
    """
    Validate a SequencingRun object for upload to irida

    If the parser is working as intended (and has proper validation) this should never return
    a ValidationResult with a list of errors. This function should be used when building a model
    from scratch, building a new parser, and as a final redundancy on parsers.

    :param sequencing_run: SequencingRun object to validate
    :return: ValidationResult object with list of errors if any
    """
    validation_result = model.ValidationResult()

    # Validation objects
    v_sequencing_run = Validator(model.SequencingRun.uploadable_schema, allow_unknown=True)
    v_project = Validator(model.Project.uploadable_schema, allow_unknown=True)
    v_sample = Validator(model.Sample.uploadable_schema, allow_unknown=True)
    v_sequence_file = Validator(model.SequenceFile.uploadable_schema, allow_unknown=True)

    # validation is nested so we can catch multiple levels of project/sample/file errors

    # Validate base SequencingRun Object
    try:
        _validate_object(v_sequencing_run, sequencing_run)

        # Validate projects in sequencing run
        for p in sequencing_run.project_list:
            try:
                _validate_object(v_project, p)

                # Validate samples in project
                for s in p.sample_list:
                    try:
                        _validate_object(v_sample, s)

                        # Validate SequenceFile on Sample
                        _validate_object(v_sequence_file, s.sequence_file)

                        # Validate tricky sequence_file rule
                        _validate_sequence_file_names(s.sequence_file)

                    except model.exceptions.ModelValidationError as e:
                        validation_result.add_error(e)

            except model.exceptions.ModelValidationError as e:
                validation_result.add_error(e)

    except model.exceptions.ModelValidationError as e:
        validation_result.add_error(e)

    return validation_result


def validate_send_project(project):
    """
    Validates a project object when using the send_project api call

    :return: raises a ModelValidationError when project is invalid
    """

    v_project = Validator(model.Project.send_project_schema, allow_unknown=True)
    _validate_object(v_project, project)


def _validate_object(validator, o):
    if not validator.validate(o.get_dict()):
        raise model.exceptions.ModelValidationError(validator.errors, o)


def _validate_sequence_file_names(sequence_file):
    """
    Validates that sequence files that are paired end have forward/reverse identifiers in the file names

    On the first difference found between the file names, we check to see that one file has one of [F, f, 1]
    and the other file has one of [R, r, 2]

    :param sequence_file:
    :return: raises a ModelValidationError when sequence_file is invalid
    """
    # Only applies to paired end files
    if not sequence_file.is_paired_end():
        return

    forward = ['F', 'f', '1']
    reverse = ['R', 'r', '2']

    file_list = sequence_file.file_list
    for letter_a, letter_b in zip(file_list[0], file_list[1]):
        if letter_a != letter_b:
            if ((letter_a in forward) and (letter_b in reverse)) or\
               ((letter_b in forward) and (letter_a in reverse)):
                return
            else:
                raise model.exceptions.ModelValidationError("Sequence File names are invalid. "
                                                            "First letter that is different between files should "
                                                            "identify forward/reverse with one of ['F', 'f', '1'] and "
                                                            "['R', 'r', '2'] respectively.", sequence_file)
