'use client';

import { deleteDataSource } from "../../../../actions/data-source.actions";
import { FormStatusButton } from "../../../../lib/components/form-status-button";

export function DeleteSource({
    sourceId,
    projectId,
}: {
    sourceId: string;
    projectId: string;
}) {
    function handleDelete() {
        if (window.confirm('Are you sure you want to delete this data source?')) {
            deleteDataSource(sourceId, projectId);
        }
    }

    return <form action={handleDelete}>
        <FormStatusButton
            props={{
                type: "submit",
                children: "Delete data source",
                className: "text-red-800",
            }}
        />
    </form>;
}