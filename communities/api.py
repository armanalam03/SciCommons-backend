from typing import Optional

from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from ninja import File, Router, UploadedFile
from ninja.errors import HttpRequest

from communities.models import Community
from communities.schemas import (
    CommunityCreateSchema,
    CommunityOut,
    CommunityUpdateSchema,
    PaginatedCommunities,
)
from myapp.schemas import Message
from users.auth import JWTAuth
from users.models import Hashtag, HashtagRelation

router = Router(tags=["Communities"])


"""
Community Management Endpoints
"""


@router.post(
    "/communities/",
    response={201: CommunityOut, 400: Message, 500: Message},
    auth=JWTAuth(),
)
def create_community(
    request: HttpRequest,
    payload: CommunityCreateSchema,
    profile_image_file: File[UploadedFile] = None,
):
    # Retrieve the authenticated user from the JWT token
    user = request.auth

    if Community.objects.filter(admins=user).exists():
        return 400, {"message": "You can only create one community."}

    # Validate the provided data and create a new Community
    new_community = Community.objects.create(
        name=payload.details.name,
        description=payload.details.description,
        type=payload.details.type,
        profile_pic_url=profile_image_file,
    )

    # Create Tags
    content_type = ContentType.objects.get_for_model(Community)

    for hashtag_name in payload.details.tags:
        hashtag, created = Hashtag.objects.get_or_create(name=hashtag_name.lower())
        HashtagRelation.objects.create(
            hashtag=hashtag, content_type=content_type, object_id=new_community.id
        )

    new_community.admins.add(user)  # Add the creator as an admin
    new_community.members.add(user)  # Add the creator as a member

    return 201, CommunityOut.from_orm_with_custom_fields(new_community, user)


@router.get(
    "/",
    response={
        200: PaginatedCommunities,
        400: Message,
        500: Message,
    },
    summary="Get Communities",
)
def list_communities(
    request: HttpRequest,
    search: Optional[str] = None,
    sort: Optional[str] = None,
    page: int = 1,
    per_page: int = 10,
):
    # Start with all non-hidden communities
    communities = Community.objects.filter(~Q(type="hidden"))

    # Apply search if provided
    if search:
        communities = communities.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )

    # Apply sorting
    if sort:
        if sort == "latest":
            communities = communities.order_by("-created_at")
        elif sort == "oldest":
            communities = communities.order_by("created_at")
        elif sort == "name_asc":
            communities = communities.order_by("name")
        elif sort == "name_desc":
            communities = communities.order_by("-name")
        # Add more sorting options if needed
    else:
        # Default sort by latest
        communities = communities.order_by("-created_at")

    paginator = Paginator(communities, per_page)
    paginated_communities = paginator.get_page(page)

    results = [
        CommunityOut.from_orm_with_custom_fields(community)
        for community in paginated_communities.object_list
    ]

    return 200, PaginatedCommunities(
        items=results,
        total=paginator.count,
        page=page,
        per_page=per_page,
        num_pages=paginator.num_pages,
    )


@router.get(
    "/community/{community_name}/",
    response={200: CommunityOut, 400: Message, 500: Message},
    auth=JWTAuth(),
)
def get_community(request, community_name: str):
    community = Community.objects.get(name=community_name)
    user = request.auth

    if community.type == "hidden" and not community.is_member(user):
        return 403, {"message": "You do not have permission to view this community."}

    return 200, CommunityOut.from_orm_with_custom_fields(community, user)


@router.put(
    "/{community_id}/",
    response={200: CommunityOut, 400: Message, 500: Message},
    auth=JWTAuth(),
)
def update_community(
    request: HttpRequest,
    community_id: int,
    payload: CommunityUpdateSchema,
    profile_pic_file: File[UploadedFile] = None,
    banner_pic_file: File[UploadedFile] = None,
):
    community = Community.objects.get(id=community_id)

    # Check if the user is an admin of this community
    if not community.admins.filter(id=request.auth.id).exists():
        return 403, {"message": "You do not have permission to modify this community."}

    # Update fields
    community.description = payload.details.description
    community.type = payload.details.type
    community.rules = payload.details.rules
    community.about = payload.details.about

    # Update Tags
    content_type = ContentType.objects.get_for_model(Community)
    HashtagRelation.objects.filter(
        content_type=content_type, object_id=community.id
    ).delete()
    for hashtag_name in payload.details.tags:
        hashtag, created = Hashtag.objects.get_or_create(name=hashtag_name.lower())
        HashtagRelation.objects.create(
            hashtag=hashtag, content_type=content_type, object_id=community.id
        )

    if banner_pic_file:
        community.banner_pic_url = banner_pic_file
    if profile_pic_file:
        community.profile_pic_url = profile_pic_file

    community.save()

    return 200, CommunityOut.from_orm_with_custom_fields(community, request.auth)


@router.delete("/{community_id}/", response={204: None}, auth=JWTAuth())
def delete_community(request: HttpRequest, community_id: int):
    community = Community.objects.get(id=community_id)

    # Check if the user is an admin of this community
    if not community.admins.filter(id=request.auth.id).exists():
        return 403, {"message": "You do not have permission to delete this community."}

    # Todo: Do not delete the community, just mark it as deleted
    community.delete()

    return 204, None
