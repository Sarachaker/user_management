"""
This Python file is part of a FastAPI application, demonstrating user management functionalities including creating, reading,
updating, and deleting (CRUD) user information. It uses OAuth2 with Password Flow for security, ensuring that only authenticated
users can perform certain operations. Additionally, the file showcases the integration of FastAPI with SQLAlchemy for asynchronous
database operations, enhancing performance by non-blocking database calls.

The implementation emphasizes RESTful API principles, with endpoints for each CRUD operation and the use of HTTP status codes
and exceptions to communicate the outcome of operations. It introduces the concept of HATEOAS (Hypermedia as the Engine of
Application State) by including navigational links in API responses, allowing clients to discover other related operations dynamically.

OAuth2PasswordBearer is employed to extract the token from the Authorization header and verify the user's identity, providing a layer
of security to the operations that manipulate user data.

Key Highlights:
- Use of FastAPI's Dependency Injection system to manage database sessions and user authentication.
- Demonstrates how to perform CRUD operations in an asynchronous manner using SQLAlchemy with FastAPI.
- Implements HATEOAS by generating dynamic links for user-related actions, enhancing API discoverability.
- Utilizes OAuth2PasswordBearer for securing API endpoints, requiring valid access tokens for operations.
"""

from builtins import dict, int, len, str
from datetime import timedelta
from io import BytesIO
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status, Request, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import logging

from app.dependencies import get_current_user, get_db, get_email_service, require_role, get_settings
from app.schemas.token_schema import TokenResponse
from app.schemas.user_schemas import UserCreate, UserListResponse, UserResponse, UserUpdate
from app.services.user_service import UserService
from app.services.jwt_service import create_access_token
from app.utils.link_generation import create_user_links, generate_pagination_links
from app.utils.minio import ProfileImageService, generate_presigned_url
from app.models.user_model import User

logger = logging.getLogger(__name__)
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
settings = get_settings()
image_service = ProfileImageService()

@router.get(
    "/users/{user_id}", response_model=UserResponse,
    name="get_user", tags=["User Management"]
)
async def get_user(
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(["ADMIN", "MANAGER"]))
):
    user = await UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_construct(
        **user.__dict__, links=create_user_links(user.id, request)
    )

@router.post(
    "/users/", response_model=UserResponse, status_code=201,
    name="create_user", tags=["User Management"]
)
async def create_user(
    user_in: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    email_service=Depends(get_email_service),
    _=Depends(require_role(["ADMIN", "MANAGER"]))
):
    if await UserService.get_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already exists")
    user = await UserService.create(db, user_in.model_dump(), email_service)
    return UserResponse.model_construct(
        **user.__dict__, links=create_user_links(user.id, request)
    )

@router.put(
    "/users/{user_id}", response_model=UserResponse,
    name="update_user", tags=["User Management"]
)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(["ADMIN", "MANAGER"]))
):
    updated = await UserService.update(db, user_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_construct(
        **updated.__dict__, links=create_user_links(updated.id, request)
    )

@router.delete(
    "/users/{user_id}", status_code=204,
    name="delete_user", tags=["User Management"]
)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(["ADMIN", "MANAGER"]))
):
    if not await UserService.delete(db, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get(
    "/users/", response_model=UserListResponse,
    name="list_users", tags=["User Management"]
)
async def list_users(
    request: Request,
    skip: int = 0, limit: int = 10,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(["ADMIN", "MANAGER"]))
):
    total = await UserService.count(db)
    users = await UserService.list_users(db, skip, limit)
    items = [UserResponse.model_validate(u) for u in users]
    links = generate_pagination_links(request, skip, limit, total)
    return UserListResponse(items=items, total=total, page=skip//limit+1, size=len(items), links=links)

@router.post(
    "/register/", response_model=UserResponse,
    name="register", tags=["Auth"]
)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    email_service=Depends(get_email_service)
):
    user = await UserService.register_user(db, user_in.model_dump(), email_service)
    if not user:
        raise HTTPException(status_code=400, detail="Email already exists")
    return user

@router.post(
    "/login/", response_model=TokenResponse,
    name="login", tags=["Auth"]
)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    if await UserService.is_account_locked(db, form.username):
        raise HTTPException(status_code=400, detail="Account locked.")
    user = await UserService.login_user(db, form.username, form.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect credentials.")
    token = create_access_token(
        data={"sub": user.email, "role": user.role.name, "id": str(user.id)},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    return {"access_token": token, "token_type": "bearer"}

@router.get(
    "/verify-email/{user_id}/{token}", name="verify_email", tags=["Auth"]
)
async def verify_email(
    user_id: UUID, token: str,
    db: AsyncSession = Depends(get_db),
    email_service=Depends(get_email_service)
):
    if not await UserService.verify_email_with_token(db, user_id, token):
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    return {"message": "Email verified"}

@router.post(
    "/users/me/upload-profile-picture",
    name="upload_profile_picture", tags=["User Management"]
)
async def upload_profile_picture_endpoint(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    _=Depends(require_role(["ADMIN","MANAGER","AUTHENTICATED"]))
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only images allowed.")
    user_id = current_user["user_id"]
    ext = file.filename.rsplit('.',1)[-1]
    name = f"{user_id}.{ext}"
    data = await file.read()
    url = image_service.store_image(data, name)
    # update user
    stmt = select(User).where(User.id==user_id)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.profile_picture_url = url
    db.add(user); await db.commit(); await db.refresh(user)
    return {"message": "Uploaded", "profile_picture_url": url}

@router.get(
    "/profile-picture/{file_name}", name="get_profile_picture", tags=["User Management"]
)
async def fetch_profile_picture(file_name: str):
    try:
        url = generate_presigned_url(file_name)
        return {"url": url}
    except Exception as e:
        logger.error("presign failed: %s", e)
        raise HTTPException(status_code=500, detail="Cannot get URL.")