"use client";
import { WorkflowPipeline, WorkflowAgent, Workflow } from "../../../lib/types/workflow_types";
import { z } from "zod";
import { X as XIcon, Settings } from "lucide-react";
import { useState, useEffect } from "react";
import { Panel } from "@/components/common/panel-common";
import { Button as CustomButton } from "@/components/ui/button";
import { InputField } from "@/app/lib/components/input-field";
import { SectionCard } from "@/components/common/section-card";

// Common section header styles
const sectionHeaderStyles = "block text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400";

export function PipelineConfig({
    projectId,
    workflow,
    pipeline,
    usedPipelineNames,
    usedAgentNames,
    agents,
    pipelines,
    handleUpdate,
    handleClose,
}: {
    projectId: string,
    workflow: z.infer<typeof Workflow>,
    pipeline: z.infer<typeof WorkflowPipeline>,
    usedPipelineNames: Set<string>,
    usedAgentNames: Set<string>,
    agents: z.infer<typeof WorkflowAgent>[],
    pipelines: z.infer<typeof WorkflowPipeline>[],
    handleUpdate: (pipeline: z.infer<typeof WorkflowPipeline>) => void,
    handleClose: () => void,
}) {
    const [localName, setLocalName] = useState(pipeline.name);
    const [nameError, setNameError] = useState<string | null>(null);
    const [showSavedBanner, setShowSavedBanner] = useState(false);

    // Function to show saved banner
    const showSavedMessage = () => {
        setShowSavedBanner(true);
        setTimeout(() => setShowSavedBanner(false), 2000);
    };

    useEffect(() => {
        setLocalName(pipeline.name);
    }, [pipeline.name]);

    const validateName = (value: string) => {
        if (value.length === 0) {
            setNameError("名称不能为空");
            return false;
        }
        // Check for conflicts with other pipeline names
        if (value !== pipeline.name && usedPipelineNames.has(value)) {
            setNameError("此名称已被其他管道使用");
            return false;
        }
        // Check for conflicts with agent names
        if (usedAgentNames.has(value)) {
            setNameError("此名称已被智能体使用");
            return false;
        }
        if (!/^[a-zA-Z0-9_-\s]+$/.test(value)) {
            setNameError("名称只能包含字母、数字、下划线、连字符和空格");
            return false;
        }
        setNameError(null);
        return true;
    };

    const handleNameChange = (value: string) => {
        setLocalName(value);
        
        if (validateName(value)) {
            handleUpdate({
                ...pipeline,
                name: value
            });
        }
        showSavedMessage();
    };

    return (
        <Panel 
            title={
                <div className="flex items-center justify-between w-full">
                    <div className="text-base font-semibold text-gray-900 dark:text-gray-100">
                        {pipeline.name}
                    </div>
                    <CustomButton
                        variant="secondary"
                        size="sm"
                        onClick={handleClose}
                        showHoverContent={true}
                        hoverContent="关闭"
                    >
                        <XIcon className="w-4 h-4" />
                    </CustomButton>
                </div>
            }
        >
            <div className="flex flex-col gap-6 p-4 h-[calc(100vh-100px)] min-h-0 flex-1">
                {/* Saved Banner */}
                {showSavedBanner && (
                    <div className="absolute top-4 left-4 z-10 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2 animate-in slide-in-from-top-2 duration-300">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        <span className="text-sm font-medium">更改已保存</span>
                    </div>
                )}

                {/* Pipeline Configuration */}
                <div className="flex flex-col gap-4 pb-4 pt-0">
                    {/* Identity Section Card */}
                    <SectionCard
                        icon={<Settings className="w-5 h-5 text-indigo-500" />}
                        title="身份"
                        labelWidth="md:w-32"
                        className="mb-1"
                    >
                        <div className="flex flex-col gap-6">
                            <div className="flex flex-col md:flex-row md:items-start gap-1 md:gap-0">
                                <label className="text-sm font-semibold text-gray-600 dark:text-gray-300 md:w-32 mb-1 md:mb-0 md:pr-4">名称</label>
                                <div className="flex-1">
                                    <InputField
                                        type="text"
                                        value={localName}
                                        onChange={handleNameChange}
                                        error={nameError}
                                        className="w-full"
                                    />
                                </div>
                            </div>
                            <div className="flex flex-col md:flex-row md:items-start gap-1 md:gap-0">
                                <label className="text-sm font-semibold text-gray-600 dark:text-gray-300 md:w-32 mb-1 md:mb-0 md:pr-4">描述</label>
                                <div className="flex-1">
                                    <InputField
                                        type="text"
                                        value={pipeline.description || ""}
                                        onChange={(value: string) => {
                                            handleUpdate({ ...pipeline, description: value });
                                            showSavedMessage();
                                        }}
                                        multiline={true}
                                        placeholder="输入此管道的描述"
                                        className="w-full"
                                    />
                                </div>
                            </div>
                        </div>
                    </SectionCard>
                    
                    {/* Pipeline Info */}
                    <SectionCard
                        icon={<Settings className="w-5 h-5 text-indigo-500" />}
                        title="行为"
                        labelWidth="md:w-32"
                        className="mb-1"
                    >
                        <div className="flex flex-col gap-4">
                            <div className="text-sm text-gray-600 dark:text-gray-400">
                                <div className="mb-2">
                                    <span className="font-medium">管道中的智能体：</span> {pipeline.agents.length}
                                </div>
                                <div className="text-xs text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/30 p-3 rounded-lg border border-blue-200 dark:border-blue-800">
                                    <div className="font-medium mb-2">管道如何工作：</div>
                                    <ul className="text-xs space-y-1 list-disc list-inside">
                                        <li>智能体按显示的顺序顺序执行</li>
                                        <li>一个智能体的输出作为下一个智能体的输入</li>
                                        <li>从智能体面板向此管道添加智能体</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </SectionCard>
                </div>
            </div>
        </Panel>
    );
} 