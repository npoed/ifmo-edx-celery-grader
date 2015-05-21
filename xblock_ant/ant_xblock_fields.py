from xblock.fields import Scope, Integer, String, Float, DateTime


class AntXBlockFields(object):

    display_name = String(
        display_name="Display name",
        default='AcademicNT Assignment',
        help="This name appears in the horizontal navigation at the top of "
             "the page.",
        scope=Scope.settings
    )

    content = String(
        display_name="Content",
        default='',
        help="Text.",
        scope=Scope.settings
    )

    points = Float(
        default=0,
        scope=Scope.user_state,
    )

    weight = Float(
        display_name="Problem Weight",
        help=("Defines the number of points each problem is worth. "
              "If the value is not set, the problem is worth the sum of the "
              "option point values."),
        values={"min": 0, "step": .1},
        default = 1,
        scope=Scope.settings
    )

    ant_course_id = String(
        display_name="Course id",
        default='',
        help="Course id in ant.",
        scope=Scope.settings
    )

    ant_unit_id = String(
        display_name="Course id",
        default='',
        help="Unit id in ant.",
        scope=Scope.settings
    )

    ant_time_limit = Integer(
        display_name="Time limit",
        default=0,
        help="Time limit (in minutes)",
        scope=Scope.settings
    )

    ant_attempts_limit = Integer(
        default=0,
        help="Submission id",
        scope=Scope.settings,
    )

    ant_status = String(
        scope=Scope.user_state,
    )

    limit_renewal = DateTime(
        display_name="Limits renewal",
        help="When limits have been renewed.",
        default=None,
        scope=Scope.settings
    )

    score = Float(
        display_name="Grade score",
        default=0,
        help="Total calculated score.",
        scope=Scope.user_state
    )

    attempts = Integer(
        display_name="Attempts used",
        default=0,
        help="Total used attempts.",
        scope=Scope.user_state
    )

    celery_task_id = String(
        display_name="Task id",
        default="",
        scope=Scope.user_state
    )

    ant_result = String(
        display_name="Latest ANT result",
        default="",
        help="Latest result retrieved by grade() method",
        scope=Scope.user_state
    )