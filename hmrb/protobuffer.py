from typing import Any, Dict, ItemsView, List, Tuple, Union

import hmrb.response_pb2 as pb


class Responses:
    """
    Class wrapper handling Responses message protobuffers

    Class for creating, holding and merging Response type protobuffer messages
    with other defined types of messages (see response.proto for protocol
    buffer definitions). Initializing the class creates an empty Responses
    protobuffer.
    Addition of data is handled through the += (__iadd__) magic method.

    Protobuffer definition (proto3):
        message Responses {
            repeated Match items = 1;                                         \
        }

    Public methods:
        +=          --   handles the addition of a new protobuffer to the object
        set_start   --   sets the start of all (not set) span messages
        get_depth   --   returns the maximum depth reached
    """

    def __init__(self) -> None:
        self.proto_responses = pb.Responses()
        self.active = True
        self.depth_reached = 0
        self.orphan_labels = None

    def __iadd__(self, other: Any) -> Any:
        """
        Adds a new message to the Responses protobuffer

        Implementation:
            Adding Labels:
                We add all the incoming labels to all (non-closed) matches,
                where a closed match is defined as having it's span.start set.

            Adding an active Match:
                An incoming active Match object inherits the labels of all
                other Match protobuffers of the Response object.
                It also picks up any orphan_labels (labels captured within
                Vars that are not yet attached to a Match, see next paragraph).

            Adding an inactive Match with depth_reached:
                An inactive Match with depth_reached set needs to transfer its
                labels to the Responses object. If the Responses protobuffer
                already contains Matches, the last non-closed Match should pick
                up the labels from the inactive Match. If no such Match exists,
                we store the labels in orphan_labels variable.

            Adding an inactive Match with no depth_reached:
                These are by definition ignored.

            Adding Responses:
                This is simply picking up all Matches not already in the
                current Responses object.

            Mirroring depth:
                At each merging of objects, the maximum of depth_reached
                counter is passed to return object.

        Args:
            other (object)  --  a wrapper class of Responses, Match or Labels

        Returns: self (Responses) object with data from other object added.

        """
        if isinstance(other, Labels):
            for item in self.proto_responses.matches:
                if not item.span.start:
                    mirror_labels(item.underscore["labels"], other)
            return self
        if isinstance(other, Match) and other.active:
            if self.orphan_labels:
                other += self.orphan_labels.underscore["labels"]
                self.orphan_labels = None
            for item in self.proto_responses.matches:
                if len(item.underscore):
                    other += item.underscore["labels"]
            self.proto_responses.matches.extend([other.proto_match])
        elif (
            isinstance(other, Match)
            and other.depth_reached
            and other.proto_match
            and len(other.proto_match.underscore)
        ):
            for item in reversed(self.proto_responses.matches):
                if not item.span.start:
                    mirror_labels(
                        item.underscore["labels"],
                        other.proto_match.underscore["labels"],
                    )
                    mirror_depth(self, other)
                    return self
            # ? sequence of orphaned_labels not captured
            self.orphan_labels = other.proto_match
        elif isinstance(other, Responses):
            for item in other.proto_responses.matches:
                if item not in self.proto_responses.matches:
                    # ? orphaned_labels are not transfered
                    self.proto_responses.matches.extend([item])
        mirror_depth(self, other)
        return self

    def set_start(self, start: int) -> None:
        for match in self.proto_responses.matches:
            if not match.span.start:
                match.span.start = str(start)

    def get_depth(self) -> int:
        depth = 0
        if self.proto_responses.matches:
            depth = int(
                max(
                    self.proto_responses.matches, key=lambda x: int(x.span.end)
                ).span.end
            )
        elif self.depth_reached and self.depth_reached > depth:
            depth = self.depth_reached
        return depth

    def set_depth(self, depth: int) -> None:
        if not self.depth_reached or depth > self.depth_reached:
            self.depth_reached = depth

    def format(
        self, sort_length: bool = False
    ) -> Union[
        List[Tuple[Tuple[int, int], List[Dict]]],
        ItemsView[Tuple[int, int], List[Dict]],
    ]:
        responses: Dict = {}
        for match in self.proto_responses.matches:
            loc = (int(match.span.start), int(match.span.end))
            atts = {k: v for k, v in match.attributes.items()}
            underscore_atts = {}
            for key, value in match.underscore.items():
                if key == "labels":
                    labels = pb.Labels()
                    value.Unpack(labels)
                    underscore_atts[key] = {
                        key: (int(value.start), int(value.end))
                        for key, value in labels.items.items()
                    }
            if loc in responses:
                responses[loc].append(atts)
            else:
                responses[loc] = [atts]
            if underscore_atts:
                responses[loc][-1].update({"_": underscore_atts})
        if sort_length:
            return sorted(responses.items(), key=lambda x: x[0][1] - x[0][0])
        return responses.items()


class Match:
    """
    Class wrapper handling Match message protobuffers

    Class for creating, holding and merging Match type protobuffer messages
    with other defined types of messages.
    Initialization of the class creates a new Match message. The Match is
    considered Active if it contains any valid attributes. Inactive Matches
    are later ignored in merging objects. An inactive Match with depth_reached
    transfers its depth_reached to the new object.
    Addition of data is handled through the += (__iadd__) magic method.

    Protobuffer definition (proto3):
        message Match {
            Span span = 1;
            map<string, string> attributes = 2;
            map<string, google.protobuf.Any> underscore = 3;                  \
        }
        message Span {
            string start = 1;
            string end = 2;                                                   \
        }

    Args:
        attributes (dict)   --   a dictionary containing all attributes
                                (except reserved attributes that are added
                                to underscore)
        depth (int)         --   current depth (also by definition the ending
                                of the Match span)

    Public methods:
        +=          --   handles the addition of a new protobuffer to the object
        set_depth   --   sets depth reached
        get_depth   --   returns the maximum depth reached

    Notes:
        span start and end integers are stored as strings, since protobuffers
        are not able to distinguish between set 0 and unset (default) 0. See
        Google's protobuffer documentation on default values.
    """

    def __init__(self, attributes: Dict, depth: int):
        self.active = bool(attributes)
        if self.active:
            self.proto_match = pb.Match()
            self.proto_match.attributes.update(attributes)
            self.proto_match.span.end = str(depth)
        else:
            self.proto_match = None
            self.span_end = str(depth)
        self.depth_reached = 0

    def __iadd__(self, other: Any) -> Any:
        """
        Adds a new message to the Match protobuffer

        Implementation:
            Adding Labels:
                We merge the Labels into the Match's existing labels.

            Adding an active Match while this Match is active:
                A new Responses object is created and returned
                holding both active Matches.

            Adding an active Match while this Match is inactive:
                The incoming active Match merges with the current Match.
                The current Match becomes active.

            Adding an inactive Match with depth_reached:
                We transfer the inactive Match's labels to the current Match.

            Adding an inactive Match with no depth_reached:
                These are by definition ignored.

            Adding Responses:
                This is handled by adding this Match to the Responses object
                and returnin the Responses object.

            Mirroring depth:
                At each merging of objects, the maximum of depth_reached
                counter is passed to return object.

        Args:
            other (object)  --  a wrapper class of Responses, Match or Labels

        Returns: self (Match or Responses) object with data from other object
                 added.

        """
        if isinstance(other, Responses):
            other += self
            return other
        elif isinstance(other, Match):
            mirror_depth(self, other)
            if self.active and other.active:
                responses = Responses()
                mirror_depth(responses, self)
                responses.proto_responses.matches.extend(
                    [self.proto_match, other.proto_match]
                )
                return responses
            elif other.active:
                self.active = True
                if self.proto_match:
                    self.proto_match.MergeFrom(other.proto_match)
                else:
                    self.proto_match = other.proto_match
            elif (
                other.depth_reached
                and other.proto_match
                and len(other.proto_match.underscore)
            ):
                if not self.proto_match:
                    self.proto_match = pb.Match()
                    self.proto_match.span.end = str(other.depth_reached)
                mirror_labels(
                    self.proto_match.underscore["labels"],
                    other.proto_match.underscore["labels"],
                )
        elif isinstance(other, Labels):
            if not self.proto_match:
                self.proto_match = pb.Match()
                self.proto_match.span.end = self.span_end
            other += self.proto_match.underscore["labels"]
            self.proto_match.underscore["labels"].Pack(other.proto_labels)
        elif other.Is(pb.Labels.DESCRIPTOR):
            mirror_labels(self.proto_match.underscore["labels"], other)
        return self

    def get_depth(self) -> int:
        if self.proto_match:
            depth = int(self.proto_match.span.end)
        else:
            depth = int(self.span_end)
        if self.depth_reached and self.depth_reached > depth:
            depth = self.depth_reached
        return depth

    def set_depth(self, depth: int) -> None:
        if not self.depth_reached or depth > self.depth_reached:
            self.depth_reached = depth

    def set_start(self, start: int) -> None:
        if self.proto_match and not self.proto_match.span.start:
            self.proto_match.span.start = str(start)


class Labels:
    """
    Class wrapper handling Labels message protobuffer

    Class for creating, holding and merging Labels type protobuffer messages
    with other defined types of messages.
    Initialization of the class creates a new Labels message.
    Addition of new Labels is handled through the += (__iadd__) magic method.

    Protobuffer definition (proto3):
        message Labels {
            map<string, Span> items = 1;                                      \
        }
        message Span {
            string start = 1;
            string end = 2;                                                   \
        }

    Args:
        labels (list)       --   a list of label names
        depth (int)         --   current depth (also by definition the ending
                                 of the Match span)
        length (int)        --   length of the object that is being labeled
                                 (defaults to 1)

    Public methods:
        +=          --   handles the addition of a new protobuffer to the object
        get_depth   --   returns the maximum depth reached

    Notes:
        span start and end integers are stored as strings, since protobuffers
        are not able to distinguish between set 0 and unset (default) 0. See
        Google's protobuffer documentation on default values.
    """

    def __init__(self, labels: set, depth: int, length: int = 1):
        self.proto_labels = pb.Labels()
        for label in labels:
            setattr(
                self.proto_labels.items[label[:-2]],
                "start" if label[-2:] == "_B" else "end",
                str(depth - length) if label[-2:] == "_B" else str(depth),
            )

    def __iadd__(self, other: Any) -> Any:
        if other.Is(pb.Labels.DESCRIPTOR):
            other_labels = pb.Labels()
            other.Unpack(other_labels)
            for key in self.proto_labels.items:
                if key in other_labels.items:
                    other_labels.items[key].MergeFrom(self.proto_labels.items[key])
            self.proto_labels.MergeFrom(other_labels)
        return self


def mirror_depth(left: Union[Match, Responses], right: Union[Match, Responses]) -> None:
    left.depth_reached = max(left.depth_reached, right.depth_reached)


def mirror_labels(left: Any, right: Any) -> None:
    left_labels = pb.Labels()
    right_labels = pb.Labels()
    if isinstance(right, Labels):
        right_labels.CopyFrom(right.proto_labels)
    elif right.Is(pb.Labels.DESCRIPTOR):
        right.Unpack(right_labels)
    left.Unpack(left_labels)
    for key in left_labels.items:
        if key in right_labels.items:
            right_labels.items[key].MergeFrom(left_labels.items[key])
    left_labels.MergeFrom(right_labels)
    left.Pack(left_labels)
