"use client";
import { DataSource } from "@/src/entities/models/data-source";
import { z } from "zod";
import { XIcon, FileIcon, GlobeIcon, AlertTriangle, CheckCircle, Circle, ExternalLinkIcon, Type, PlusIcon, Edit3Icon, DownloadIcon, Trash2 } from "lucide-react";
import { useState, useEffect, useCallback } from "react";
import { Panel } from "@/components/common/panel-common";
import { Button } from "@/components/ui/button";
import { DataSourceIcon } from "@/app/lib/components/datasource-icon";
import { Tooltip } from "@heroui/react";
import { getDataSource, listDocsInDataSource, deleteDocFromDataSource, getDownloadUrlForFile, addDocsToDataSource, getUploadUrlsForFilesDataSource } from "@/app/actions/data-source.actions";
import { InputField } from "@/app/lib/components/input-field";
import { DataSourceDoc } from "@/src/entities/models/data-source-doc";
import { RelativeTime } from "@primer/react";
import { Pagination, Spinner, Button as HeroButton, Textarea as HeroTextarea } from "@heroui/react";
import { useDropzone } from "react-dropzone";

export function DataSourceConfig({
    dataSourceId,
    handleClose,
    onDataSourceUpdate
}: {
    dataSourceId: string,
    handleClose: () => void,
    onDataSourceUpdate?: () => void
}) {
    const [dataSource, setDataSource] = useState<z.infer<typeof DataSource> | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    
    // Files-related state
    const [files, setFiles] = useState<z.infer<typeof DataSourceDoc>[]>([]);
    const [filesLoading, setFilesLoading] = useState(false);
    const [filesPage, setFilesPage] = useState(1);
    const [filesTotal, setFilesTotal] = useState(0);
    const [projectId, setProjectId] = useState<string>('');

    useEffect(() => {
        async function loadDataSource() {
            try {
                setLoading(true);
                // Extract projectId from the current URL
                const pathParts = window.location.pathname.split('/');
                const currentProjectId = pathParts[2]; // /projects/[projectId]/workflow
                setProjectId(currentProjectId);
                
                const ds = await getDataSource(dataSourceId, currentProjectId);
                setDataSource(ds);
                
                // Load files if it's a files data source
                if (ds.data.type === 'files_local' || ds.data.type === 'files_s3') {
                    await loadFiles(dataSourceId, 1);
                }
                
                // Load URLs if it's a URLs data source
                if (ds.data.type === 'urls') {
                    await loadUrls(dataSourceId, 1);
                }
                
                // Load text content if it's a text data source
                if (ds.data.type === 'text') {
                    await loadTextContent(dataSourceId);
                }
            } catch (err) {
                console.error('Failed to load data source:', err);
                setError('加载数据源详细信息失败');
            } finally {
                setLoading(false);
            }
        }

        loadDataSource();
    }, [dataSourceId]);

    // Auto-refresh data source status when it's pending
    useEffect(() => {
        let ignore = false;
        let timeout: NodeJS.Timeout | null = null;

        if (!dataSource || !projectId) {
            return;
        }
        
        if (dataSource.status !== 'pending') {
            return;
        }

        async function refreshStatus() {
            if (timeout) {
                clearTimeout(timeout);
            }
            
            try {
                const updatedSource = await getDataSource(dataSourceId, projectId);
                if (!ignore) {
                    setDataSource(updatedSource);
                    onDataSourceUpdate?.(); // Notify parent of status change
                    
                    // Continue polling if still pending
                    if (updatedSource.status === 'pending') {
                        timeout = setTimeout(refreshStatus, 5000); // Poll every 5 seconds
                    }
                }
            } catch (err) {
                console.error('Failed to refresh data source status:', err);
                // Retry after a longer delay on error
                if (!ignore) {
                    timeout = setTimeout(refreshStatus, 10000);
                }
            }
        }

        // Start polling after a short delay
        timeout = setTimeout(refreshStatus, 5000);

        return () => {
            ignore = true;
            if (timeout) {
                clearTimeout(timeout);
            }
        };
    }, [dataSource, projectId, dataSourceId, onDataSourceUpdate]);

    // Helper function to update data source and notify parent
    const updateDataSourceAndNotify = useCallback(async () => {
        try {
            const updatedSource = await getDataSource(dataSourceId, projectId);
            setDataSource(updatedSource);
            onDataSourceUpdate?.();
        } catch (err) {
            console.error('Failed to reload data source:', err);
        }
    }, [dataSourceId, projectId, onDataSourceUpdate]);

    // Load files function
    const loadFiles = async (sourceId: string, page: number) => {
        try {
            setFilesLoading(true);
            const { files, total } = await listDocsInDataSource({
                sourceId,
                page,
                limit: 10,
            });
            setFiles(files);
            setFilesTotal(total);
            setFilesPage(page);
        } catch (err) {
            console.error('Failed to load files:', err);
        } finally {
            setFilesLoading(false);
        }
    };

    // URLs-related state
    const [urls, setUrls] = useState<z.infer<typeof DataSourceDoc>[]>([]);
    const [urlsLoading, setUrlsLoading] = useState(false);
    const [urlsPage, setUrlsPage] = useState(1);
    const [urlsTotal, setUrlsTotal] = useState(0);

    // Text-related state
    const [textContent, setTextContent] = useState<string>('');
    const [textLoading, setTextLoading] = useState(false);
    const [savingText, setSavingText] = useState(false);
    
    // URL form state
    const [showAddUrlForm, setShowAddUrlForm] = useState(false);
    const [addingUrls, setAddingUrls] = useState(false);
    
    // File upload state
    const [uploadingFiles, setUploadingFiles] = useState(false);

    // Load URLs function
    const loadUrls = async (sourceId: string, page: number) => {
        try {
            setUrlsLoading(true);
            const { files, total } = await listDocsInDataSource({
                sourceId,
                page,
                limit: 10,
            });
            setUrls(files);
            setUrlsTotal(total);
            setUrlsPage(page);
        } catch (err) {
            console.error('Failed to load URLs:', err);
        } finally {
            setUrlsLoading(false);
        }
    };

    // Load text content function
    const loadTextContent = async (sourceId: string) => {
        try {
            setTextLoading(true);
            const { files } = await listDocsInDataSource({
                sourceId,
                limit: 1,
            });
            
            if (files.length > 0 && files[0].data.type === 'text') {
                setTextContent(files[0].data.content);
            } else {
                setTextContent('');
            }
        } catch (err) {
            console.error('Failed to load text content:', err);
            setTextContent('');
        } finally {
            setTextLoading(false);
        }
    };

    // Handle file deletion
    const handleDeleteFile = async (fileId: string) => {
        if (!window.confirm('确定要删除此文件吗？')) return;
        
        try {
            await deleteDocFromDataSource({
                docId: fileId,
            });
            // Reload files
            await loadFiles(dataSourceId, filesPage);
            
            // Reload data source to get updated status
            await updateDataSourceAndNotify();
        } catch (err) {
            console.error('Failed to delete file:', err);
        }
    };

    // Handle file download
    const handleDownloadFile = async (fileId: string) => {
        try {
            const url = await getDownloadUrlForFile(fileId);
            window.open(url, '_blank');
        } catch (err) {
            console.error('Failed to download file:', err);
        }
    };

    // Handle page change
    const handlePageChange = (page: number) => {
        loadFiles(dataSourceId, page);
    };

    // Handle URL deletion
    const handleDeleteUrl = async (urlId: string) => {
        if (!window.confirm('确定要删除此URL吗？')) return;
        
        try {
            await deleteDocFromDataSource({
                docId: urlId,
            });
            // Reload URLs
            await loadUrls(dataSourceId, urlsPage);
            
            // Reload data source to get updated status
            await updateDataSourceAndNotify();
        } catch (err) {
            console.error('删除URL失败:', err);
        }
    };

    // Handle URL page change
    const handleUrlPageChange = (page: number) => {
        loadUrls(dataSourceId, page);
    };

    // Handle text content update
    const handleUpdateTextContent = async (newContent: string) => {
        setSavingText(true);
        try {
            // Delete existing text doc if it exists
            const { files } = await listDocsInDataSource({
                sourceId: dataSourceId,
                limit: 1,
            });
            
            if (files.length > 0) {
                await deleteDocFromDataSource({
                    docId: files[0].id,
                });
            }

            // Add new text doc
            await addDocsToDataSource({
                sourceId: dataSourceId,
                docData: [{
                    name: 'text',
                    data: {
                        type: 'text',
                        content: newContent,
                    },
                }],
            });

            setTextContent(newContent);
            
            // Reload data source to get updated status
            await updateDataSourceAndNotify();
        } catch (err) {
            console.error('保存文本失败:', err);
        } finally {
            setSavingText(false);
        }
    };

    // Handle URL addition
    const handleAddUrls = async (formData: FormData) => {
        setAddingUrls(true);
        try {
            const urls = formData.get('urls') as string;
            const urlsArray = urls.split('\n')
                .map(url => url.trim())
                .filter(url => url.length > 0);
            const first100Urls = urlsArray.slice(0, 100);
            
            await addDocsToDataSource({
                sourceId: dataSourceId,
                docData: first100Urls.map(url => ({
                    name: url,
                    data: {
                        type: 'url',
                        url,
                    },
                })),
            });
            
            setShowAddUrlForm(false);
            await loadUrls(dataSourceId, urlsPage);
            
            // Reload data source to get updated status
            await updateDataSourceAndNotify();
        } catch (err) {
            console.error('添加URL失败:', err);
        } finally {
            setAddingUrls(false);
        }
    };

    // Handle file upload
    const onFileDrop = useCallback(async (acceptedFiles: File[]) => {
        if (!dataSource) return;
        
        setUploadingFiles(true);
        try {
            const urls = await getUploadUrlsForFilesDataSource(dataSourceId, acceptedFiles.map(file => ({
                name: file.name,
                type: file.type,
                size: file.size,
            })));

            // Upload files in parallel
            await Promise.all(acceptedFiles.map(async (file, index) => {
                await fetch(urls[index].uploadUrl, {
                    method: 'PUT',
                    body: file,
                    headers: {
                        'Content-Type': file.type,
                    },
                });
            }));

            // After successful uploads, update the database with file information
            let docData: {
                _id: string,
                name: string,
                data: z.infer<typeof DataSourceDoc>['data']
            }[] = [];
            
            const isS3 = dataSource.data.type === 'files_s3';
            
            if (isS3) {
                docData = acceptedFiles.map((file, index) => ({
                    _id: urls[index].fileId,
                    name: file.name,
                    data: {
                        type: 'file_s3' as const,
                        name: file.name,
                        size: file.size,
                        mimeType: file.type,
                        s3Key: urls[index].path,
                    },
                }));
            } else {
                docData = acceptedFiles.map((file, index) => ({
                    _id: urls[index].fileId,
                    name: file.name,
                    data: {
                        type: 'file_local' as const,
                        name: file.name,
                        size: file.size,
                        mimeType: file.type,
                        path: urls[index].path,
                    },
                }));
            }

            await addDocsToDataSource({
                sourceId: dataSourceId,
                docData,
            });

            await loadFiles(dataSourceId, filesPage);
            
            // Reload data source to get updated status
            await updateDataSourceAndNotify();
        } catch (error) {
            console.error('Upload failed:', error);
        } finally {
            setUploadingFiles(false);
        }
    }, [dataSourceId, dataSource, filesPage, updateDataSourceAndNotify]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop: onFileDrop,
        disabled: uploadingFiles,
        accept: {
            'application/pdf': ['.pdf'],
        },
    });

    if (loading) {
        return (
            <Panel
                title={
                    <div className="flex items-center justify-between w-full">
                        <div className="text-base font-semibold text-gray-900 dark:text-gray-100">
                            加载数据源...
                        </div>
                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={handleClose}
                            showHoverContent={true}
                            hoverContent="关闭"
                        >
                            <XIcon className="w-4 h-4" />
                        </Button>
                    </div>
                }
            >
                <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                </div>
            </Panel>
        );
    }

    if (error || !dataSource) {
        return (
            <Panel
                title={
                    <div className="flex items-center justify-between w-full">
                        <div className="text-base font-semibold text-gray-900 dark:text-gray-100">
                            加载数据源错误
                        </div>
                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={handleClose}
                            showHoverContent={true}
                            hoverContent="关闭"
                        >
                            <XIcon className="w-4 h-4" />
                        </Button>
                    </div>
                }
            >
                <div className="flex items-center justify-center h-64 text-red-500">
                    <div className="text-center">
                        <AlertTriangle className="w-12 h-12 mx-auto mb-4" />
                        <p>{error || '未找到数据源'}</p>
                    </div>
                </div>
            </Panel>
        );
    }

    // Determine status
    const isActive = dataSource.active && dataSource.status === 'ready';
    const isPending = dataSource.status === 'pending';
    const isError = dataSource.status === 'error';

    // Status indicator
    const statusIndicator = () => {
        if (isPending) {
            return (
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-yellow-50 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400">
                    <Spinner size="sm" color="warning" />
                    <span className="text-sm font-medium">处理中</span>
                </div>
            );
        } else if (isError) {
            return (
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400">
                    <AlertTriangle className="w-4 h-4" />
                    <span className="text-sm font-medium">错误</span>
                </div>
            );
        } else if (isActive) {
            return (
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400">
                    <CheckCircle className="w-4 h-4" />
                    <span className="text-sm font-medium">激活</span>
                </div>
            );
        } else {
            return (
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-gray-50 text-gray-700 dark:bg-gray-900/20 dark:text-gray-400">
                    <Circle className="w-4 h-4" />
                    <span className="text-sm font-medium">未激活</span>
                </div>
            );
        }
    };

    // Type display name
    const getTypeDisplayName = (type: string) => {
        switch (type) {
            case 'urls': return '抓取的URL';
            case 'files_local': return '本地文件';
            case 'files_s3': return 'S3文件';
            case 'text': return '文本内容';
            default: return type;
        }
    };

    return (
        <Panel
            title={
                <div className="flex items-center justify-between w-full">
                    <div className="flex items-center gap-3">
                        <DataSourceIcon 
                            type={
                                dataSource.data.type === 'files_local' || dataSource.data.type === 'files_s3' 
                                    ? 'files' 
                                    : dataSource.data.type
                            } 
                            size="md" 
                        />
                        <div>
                            <div className="text-base font-semibold text-gray-900 dark:text-gray-100">
                                {dataSource.name}
                            </div>
                            <div className="text-sm text-gray-500 dark:text-gray-400">
                                数据源
                            </div>
                        </div>
                    </div>
                    <Button
                        variant="secondary"
                        size="sm"
                        onClick={handleClose}
                        showHoverContent={true}
                        hoverContent="关闭"
                    >
                        <XIcon className="w-4 h-4" />
                    </Button>
                </div>
            }
        >
            <div className="h-full overflow-auto">
                <div className="p-6 space-y-6">
                    {/* Status Section */}
                    <div className="space-y-3">
                        <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">状态</h3>
                        {statusIndicator()}
                        {isError && dataSource.error && (
                            <div className="mt-2 p-3 bg-red-50 dark:bg-red-900/20 rounded-md">
                                <p className="text-sm text-red-700 dark:text-red-400">{dataSource.error}</p>
                            </div>
                        )}
                    </div>

                    {/* Basic Information */}
                    <div className="space-y-3">
                        <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">信息</h3>
                        <div className="grid grid-cols-1 gap-4 text-sm">
                            <div className="flex justify-between">
                                <span className="text-gray-500 dark:text-gray-400">类型：</span>
                                <span className="text-gray-900 dark:text-gray-100">{getTypeDisplayName(dataSource.data.type)}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-gray-500 dark:text-gray-400">状态：</span>
                                <div className="flex items-center">
                                    {statusIndicator()}
                                </div>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-500 dark:text-gray-400">创建时间：</span>
                                <span className="text-gray-900 dark:text-gray-100">
                                    {new Date(dataSource.createdAt).toLocaleDateString()}
                                </span>
                            </div>
                            {dataSource.lastUpdatedAt && (
                                <div className="flex justify-between">
                                    <span className="text-gray-500 dark:text-gray-400">最后更新：</span>
                                    <span className="text-gray-900 dark:text-gray-100">
                                        {new Date(dataSource.lastUpdatedAt).toLocaleDateString()}
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Description */}
                    {dataSource.description && (
                        <div className="space-y-3">
                            <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">描述</h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 p-3 rounded-md">
                                {dataSource.description}
                            </p>
                        </div>
                    )}

                    {/* Files Section (for file-type data sources) */}
                    {(dataSource.data.type === 'files_local' || dataSource.data.type === 'files_s3') && (
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                    文件 ({filesTotal})
                                </h3>
                            </div>

                            {/* File Upload Area */}
                            <div
                                {...getRootProps()}
                                className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors
                                    ${isDragActive ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/10' : 'border-gray-300 dark:border-gray-700'}`}
                            >
                                <input {...getInputProps()} />
                                {uploadingFiles ? (
                                    <div className="flex items-center justify-center gap-2">
                                        <Spinner size="sm" />
                                        <p className="text-sm">上传文件中...</p>
                                    </div>
                                ) : isDragActive ? (
                                    <p className="text-sm">将文件拖放到此处...</p>
                                ) : (
                                    <div className="space-y-2">
                                        <div className="flex items-center justify-center gap-2">
                                            <PlusIcon className="w-4 h-4" />
                                            <p className="text-sm">拖放文件到此处，或点击选择文件</p>
                                        </div>
                                        <p className="text-xs text-gray-500 dark:text-gray-400">
                                            目前仅支持PDF文件。
                                        </p>
                                    </div>
                                )}
                            </div>
                            
                            {filesLoading ? (
                                <div className="flex items-center justify-center gap-2 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                                    <Spinner size="sm" />
                                    <p className="text-gray-600 dark:text-gray-300">加载文件中...</p>
                                </div>
                            ) : files.length === 0 ? (
                                <div className="text-center p-8 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                                    <FileIcon className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                                    <p className="text-gray-500 dark:text-gray-400">尚未上传文件</p>
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    {files.map((file) => (
                                        <div
                                            key={file.id}
                                            className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg border"
                                        >
                                            <div className="flex items-center gap-3 flex-1 min-w-0">
                                                <FileIcon className="w-4 h-4 text-gray-500 flex-shrink-0" />
                                                <div className="min-w-0 flex-1">
                                                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                                                        {file.name}
                                                    </p>
                                                    <p className="text-xs text-gray-500 dark:text-gray-400">
                                                        <RelativeTime date={new Date(file.createdAt)} />
                                                        {file.data.type === 'file_local' && ' • 本地'}
                                                        {file.data.type === 'file_s3' && ' • S3'}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                {(file.data.type === 'file_local' || file.data.type === 'file_s3') && (
                                                    <Tooltip content="下载文件">
                                                        <button
                                                            onClick={() => handleDownloadFile(file.id)}
                                                            className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                                                        >
                                                            <DownloadIcon className="w-4 h-4 text-gray-500" />
                                                        </button>
                                                    </Tooltip>
                                                )}
                                                <Tooltip content="删除文件">
                                                    <button
                                                        onClick={() => handleDeleteFile(file.id)}
                                                        className="p-1 hover:bg-red-100 dark:hover:bg-red-900/20 rounded transition-colors"
                                                    >
                                                        <Trash2 className="w-4 h-4 text-red-500" />
                                                    </button>
                                                </Tooltip>
                                            </div>
                                        </div>
                                    ))}
                                    
                                    {/* Pagination */}
                                    {filesTotal > 10 && (
                                        <div className="flex justify-center pt-4">
                                            <Pagination
                                                total={Math.ceil(filesTotal / 10)}
                                                page={filesPage}
                                                onChange={handlePageChange}
                                                size="sm"
                                            />
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}

                    {/* URLs Section (for URL-type data sources) */}
                    {dataSource.data.type === 'urls' && (
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                    URLs ({urlsTotal})
                                </h3>
                            </div>

                            {/* Add URLs Button/Form */}
                            {!showAddUrlForm ? (
                                <HeroButton
                                    onClick={() => setShowAddUrlForm(true)}
                                    variant="bordered"
                                    size="sm"
                                    startContent={<PlusIcon className="w-4 h-4" />}
                                >
                                    添加URL
                                </HeroButton>
                            ) : (
                                <form 
                                    action={handleAddUrls}
                                    className="space-y-3 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border"
                                >
                                    <div className="space-y-2">
                                        <label className="text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                                            添加URL（每行一个）
                                        </label>
                                        <HeroTextarea
                                            required
                                            name="urls"
                                            minRows={5}
                                            placeholder="https://example.com"
                                            className="w-full"
                                        />
                                    </div>
                                    <div className="flex gap-2">
                                        <HeroButton
                                            type="submit"
                                            color="primary"
                                            size="sm"
                                            isDisabled={addingUrls}
                                            isLoading={addingUrls}
                                            startContent={!addingUrls ? <PlusIcon className="w-4 h-4" /> : undefined}
                                        >
                                            {addingUrls ? '添加中...' : '添加URL'}
                                        </HeroButton>
                                        <HeroButton
                                            type="button"
                                            variant="bordered"
                                            size="sm"
                                            onClick={() => setShowAddUrlForm(false)}
                                            isDisabled={addingUrls}
                                        >
                                            取消
                                        </HeroButton>
                                    </div>
                                </form>
                            )}
                            
                            {urlsLoading ? (
                                <div className="flex items-center justify-center gap-2 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                                    <Spinner size="sm" />
                                    <p className="text-gray-600 dark:text-gray-300">加载URL中...</p>
                                </div>
                            ) : urls.length === 0 ? (
                                <div className="text-center p-8 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                                    <GlobeIcon className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                                    <p className="text-gray-500 dark:text-gray-400">尚未添加URL</p>
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    {urls.map((url) => (
                                        <div
                                            key={url.id}
                                            className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg border"
                                        >
                                            <div className="flex items-center gap-3 flex-1 min-w-0">
                                                <GlobeIcon className="w-4 h-4 text-gray-500 flex-shrink-0" />
                                                <div className="min-w-0 flex-1">
                                                    <div className="flex items-center gap-2">
                                                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                                                            {url.name}
                                                        </p>
                                                        {url.data.type === 'url' && (
                                                            <a 
                                                                href={url.data.url} 
                                                                target="_blank" 
                                                                rel="noopener noreferrer"
                                                                className="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors"
                                                            >
                                                                <ExternalLinkIcon className="w-3.5 h-3.5" />
                                                            </a>
                                                        )}
                                                    </div>
                                                    <p className="text-xs text-gray-500 dark:text-gray-400">
                                                        <RelativeTime date={new Date(url.createdAt)} />
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Tooltip content="删除URL">
                                                    <button
                                                        onClick={() => handleDeleteUrl(url.id)}
                                                        className="p-1 hover:bg-red-100 dark:hover:bg-red-900/20 rounded transition-colors"
                                                    >
                                                        <Trash2 className="w-4 h-4 text-red-500" />
                                                    </button>
                                                </Tooltip>
                                            </div>
                                        </div>
                                    ))}
                                    
                                    {/* Pagination */}
                                    {urlsTotal > 10 && (
                                        <div className="flex justify-center pt-4">
                                            <Pagination
                                                total={Math.ceil(urlsTotal / 10)}
                                                page={urlsPage}
                                                onChange={handleUrlPageChange}
                                                size="sm"
                                            />
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Text Content Section (for text-type data sources) */}
                    {dataSource.data.type === 'text' && (
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                    文本内容
                                </h3>
                            </div>
                            
                            {textLoading ? (
                                <div className="flex items-center justify-center gap-2 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                                    <Spinner size="sm" />
                                    <p className="text-gray-600 dark:text-gray-300">加载内容中...</p>
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    <label className="text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                                        文本内容
                                    </label>
                                    <InputField
                                        type="text"
                                        value={textContent}
                                        onChange={handleUpdateTextContent}
                                        multiline={true}
                                        placeholder="在此输入文本内容"
                                        className="w-full"
                                        disabled={savingText}
                                    />
                                    {savingText && (
                                        <div className="text-xs text-gray-500 dark:text-gray-400">
                                            保存中...
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Usage Information */}
                    <div className="space-y-3">
                        <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">使用</h3>
                        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-md">
                            <div className="flex items-start gap-3">
                                <div className="w-5 h-5 text-blue-500 mt-0.5">
                                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                </div>
                                <div className="text-sm text-blue-700 dark:text-blue-300">
                                    <p className="font-medium mb-1">使用此数据源</p>
                                    <p>要在智能体中使用此数据源，请转到各个智能体设置中的RAG选项卡并连接此数据源。</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </Panel>
    );
}