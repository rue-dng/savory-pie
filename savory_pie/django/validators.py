class BaseValidator:

    """
    Validators are used to determine that the values of model fields are acceptable
    according to programmatically specifiable criteria::

        class EverybodyHatesBob(validators.ResourceValidator):
            error_message = 'Everybody hates Bob'

            def test(self, user):
                return user.name != 'Bob'

        class TooYoungToDrink(validators.FieldValidator):
            error_message = 'Too young to drink'

            def test(self, age):
                return age >= 21

        class LegalDrinkingAgeResource(resources.ModelResource):
            parent_resource_path = 'users'
            model_class = User

            validators = [
                EverybodyHatesBob()
            ]

            fields = [
                fields.AttributeField(attribute='name', type=str),
                fields.AttributeField(attribute='age', type=int, validator=TooYoungToDrink())
            ]

    Now when you call the *validate* method on an instance of LegalDrinkingAgeResource,
    it will check to see if the underlying database model has a name that isn't "Bob" and
    an age that is at least 21, and will return a dict giving all violations as key-value
    pairs, where the keys are dotted Python names for the model or field in question, and
    the values are lists of error messages. So in this case, you might see::

        {'some.package.LegalDrinkingAgeResource': ['Everybody hates Bob'],
         'some.package.LegalDrinkingAgeResource.age': ['Too young to drink']}

    """

    error_message = 'Validation failure message goes here'
    """
    The error message should give a clear description of the nature of the validation
    failure, if one occurs.
    """

    def _add_error(self, error_dict, key, error):
        if key in error_dict:
            error_dict[key].append(error)
        else:
            error_dict[key] = [error]

    def test(value):
        """
        Extend this method to test whatever needs testing on a model or field. Return
        True if the value is OK, False if it's unacceptable.
        """
        return False



class ResourceValidator(BaseValidator):

    def find_errors(self, error_dict, resource):
        """
        Search for validation errors in the database model underlying a resource.
        """
        if not self.test(resource.model):
            self._add_error(error_dict, resource.dotted_name, self.error_message)



class FieldValidator(BaseValidator):

    def find_errors(self, error_dict, resource, field):
        """
        Search for validation errors in a field of a database model.
        """
        if not self.test(getattr(resource.model, field.name)):
            self._add_error(error_dict, resource.dotted_name + '.' + field.name,
                            self.error_message)
