import { db } from "@/app/lib/mongodb";
import { CreateSchema, IProjectsRepository, AddComposioConnectedAccountSchema, AddCustomMcpServerSchema } from "@/src/application/repositories/projects.repository.interface";
import { NotFoundError } from "@/src/entities/errors/common";
import { Project } from "@/src/entities/models/project";
import { z } from "zod";
import { IProjectMembersRepository } from "@/src/application/repositories/project-members.repository.interface";
import { PaginatedList } from "@/src/entities/common/paginated-list";

const docSchema = Project
    .omit({
        id: true,
    })
    .extend({
        _id: z.string().uuid(),
        id: z.string().uuid().optional(), // 允许 id 字段，用于索引
    });

export class MongodbProjectsRepository implements IProjectsRepository {
    private readonly projectMembersRepository: IProjectMembersRepository;
    private collection = db.collection<z.infer<typeof docSchema>>('projects');

    constructor({
        projectMembersRepository,
    }: {
        projectMembersRepository: IProjectMembersRepository,
    }) {
        this.projectMembersRepository = projectMembersRepository;
    }

    async create(data: z.infer<typeof CreateSchema>): Promise<z.infer<typeof Project>> {
        const now = new Date();

        const wflow = {
            ...data.workflow,
            lastUpdatedAt: now.toISOString(),
        };

        const id = crypto.randomUUID();

        const doc = {
            ...data,
            liveWorkflow: wflow,
            draftWorkflow: wflow,
            createdAt: now.toISOString(),
        };
        
        // 插入文档时，同时设置 _id 和 id 字段
        // MongoDB 索引在 id 字段上，所以必须设置 id 字段
        const docToInsert = {
            ...doc,
            _id: id,
            id: id,  // 确保 id 字段也被设置，以满足索引要求
        } as z.infer<typeof docSchema>;
        await this.collection.insertOne(docToInsert);
        return {
            ...doc,
            id,
        };
    }

    async fetch(id: string): Promise<z.infer<typeof Project> | null> {
        // 可以按 _id 或 id 字段查询
        const doc = await this.collection.findOne({ $or: [{ _id: id }, { id: id }] });
        if (!doc) {
            return null;
        }
        // 如果文档有 id 字段，使用它；否则使用 _id
        const docId = doc.id || doc._id;
        const { _id, ...rest } = doc;
        return {
            ...rest,
            id: docId,
        };
    }

    async countCreatedProjects(createdByUserId: string): Promise<number> {
        return await this.collection.countDocuments({ createdByUserId });
    }

    async listProjects(userId: string, cursor?: string, limit?: number): Promise<z.infer<ReturnType<typeof PaginatedList<typeof Project>>>> {
        const memberships = await this.projectMembersRepository.findByUserId(userId, cursor, limit);
        const projectIds = memberships.items.map((m) => m.projectId);
        const projects = await this.collection.find({
            $or: [
                { _id: { $in: projectIds } },
                { id: { $in: projectIds } }
            ],
        }).toArray();
        return {
            items: projects.map((p) => {
                const { _id, ...rest } = p;
                const docId = p.id || p._id;
                return {
                    ...rest,
                    id: docId,  // 确保 id 字段存在，并移除 _id
                } as z.infer<typeof Project>;
            }),
            nextCursor: memberships.nextCursor,
        };
    }

    async addComposioConnectedAccount(projectId: string, data: z.infer<typeof AddComposioConnectedAccountSchema>): Promise<z.infer<typeof Project>> {
        const key = `composioConnectedAccounts.${data.toolkitSlug}`;
        const result = await this.collection.findOneAndUpdate(
            { $or: [{ _id: projectId }, { id: projectId }] },
            {
                $set: {
                    [key]: data.data,
                    lastUpdatedAt: new Date().toISOString(),
                }
            },
            { returnDocument: 'after' }
        );
        if (!result) {
            throw new NotFoundError('Project not found');
        }
        const { _id, ...rest } = result;
        return { ...rest, id: result.id || _id };
    }

    async deleteComposioConnectedAccount(projectId: string, toolkitSlug: string): Promise<boolean> {
        const result = await this.collection.updateOne({
            $or: [{ _id: projectId }, { id: projectId }]
        }, {
            $unset: {
                [`composioConnectedAccounts.${toolkitSlug}`]: "",
            }
        });
        return result.modifiedCount > 0;
    }

    async addCustomMcpServer(projectId: string, data: z.infer<typeof AddCustomMcpServerSchema>): Promise<z.infer<typeof Project>> {
        const key = `customMcpServers.${data.name}`;
        const result = await this.collection.findOneAndUpdate(
            { $or: [{ _id: projectId }, { id: projectId }] },
            {
                $set: {
                    [key]: data.data,
                    lastUpdatedAt: new Date().toISOString(),
                }
            },
            { returnDocument: 'after' }
        );
        if (!result) {
            throw new NotFoundError('Project not found');
        }
        const { _id, ...rest } = result;
        return { ...rest, id: result.id || _id };
    }

    async deleteCustomMcpServer(projectId: string, name: string): Promise<boolean> {
        const result = await this.collection.updateOne({
            $or: [{ _id: projectId }, { id: projectId }]
        }, {
            $unset: {
                [`customMcpServers.${name}`]: "",
            }
        });
        return result.modifiedCount > 0;
    }

    async updateSecret(projectId: string, secret: string): Promise<z.infer<typeof Project>> {
        const result = await this.collection.findOneAndUpdate(
            { $or: [{ _id: projectId }, { id: projectId }] },
            {
                $set: {
                    secret,
                    lastUpdatedAt: new Date().toISOString(),
                }
            },
            { returnDocument: 'after' }
        );
        if (!result) {
            throw new NotFoundError('Project not found');
        }
        const { _id, ...rest } = result;
        return { ...rest, id: result.id || _id };
    }

    async updateWebhookUrl(projectId: string, url: string): Promise<z.infer<typeof Project>> {
        const result = await this.collection.findOneAndUpdate(
            { $or: [{ _id: projectId }, { id: projectId }] },
            {
                $set: {
                    webhookUrl: url,
                    lastUpdatedAt: new Date().toISOString(),
                }
            },
            { returnDocument: 'after' }
        );
        if (!result) {
            throw new NotFoundError('Project not found');
        }
        const { _id, ...rest } = result;
        return { ...rest, id: result.id || _id };
    }

    async updateName(projectId: string, name: string): Promise<z.infer<typeof Project>> {
        const result = await this.collection.findOneAndUpdate(
            { $or: [{ _id: projectId }, { id: projectId }] },
            {
                $set: {
                    name,
                    lastUpdatedAt: new Date().toISOString(),
                }
            },
            { returnDocument: 'after' }
        );
        if (!result) {
            throw new NotFoundError('Project not found');
        }
        const { _id, ...rest } = result;
        return { ...rest, id: result.id || _id };
    }

    async updateDraftWorkflow(projectId: string, workflow: z.infer<typeof import("@/app/lib/types/workflow_types").Workflow>): Promise<z.infer<typeof Project>> {
        const result = await this.collection.findOneAndUpdate(
            { $or: [{ _id: projectId }, { id: projectId }] },
            {
                $set: {
                    draftWorkflow: workflow,
                    lastUpdatedAt: new Date().toISOString(),
                }
            },
            { returnDocument: 'after' }
        );
        if (!result) {
            throw new NotFoundError('Project not found');
        }
        const { _id, ...rest } = result;
        return { ...rest, id: result.id || _id };
    }

    async updateLiveWorkflow(projectId: string, workflow: z.infer<typeof import("@/app/lib/types/workflow_types").Workflow>): Promise<z.infer<typeof Project>> {
        const result = await this.collection.findOneAndUpdate(
            { $or: [{ _id: projectId }, { id: projectId }] },
            {
                $set: {
                    liveWorkflow: workflow,
                    lastUpdatedAt: new Date().toISOString(),
                }
            },
            { returnDocument: 'after' }
        );
        if (!result) {
            throw new NotFoundError('Project not found');
        }
        const { _id, ...rest } = result;
        return { ...rest, id: result.id || _id };
    }

    async delete(projectId: string): Promise<boolean> {
        const result = await this.collection.deleteOne({ $or: [{ _id: projectId }, { id: projectId }] });
        return result.deletedCount > 0;
    }
}